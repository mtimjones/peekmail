# PeekMail - Email summarization
# mtj@mtjones.com
# January 18th, 2025

import os
import sys
import poplib
from openai import OpenAI
from getpass import getpass
from email.parser import Parser
from email.header import decode_header


def Get_Email_Context( ) -> str:

    # Email credentials
    username = input( "Username: " )
    password = getpass( )
    popname = 'pop.'+username.split( '@', 1 )[1]

    # Connect to the POP3 server
    try:
        mail = poplib.POP3_SSL( popname )
        mail.user( username )
        mail.pass_( password )
    except:
        print("Username or password is incorrect.")
        sys.exit( 0 )

    # Get the number of messages
    num_messages = len( mail.list( )[1] )

    # Create an empty list to hold email subjects and first few lines
    emails_info = []

    # Loop through all the messages
    for i in range( num_messages ):
        # Fetch the email by index (starting from 1)
        response, lines, octets = mail.retr( i + 1 )
    
        # Join the lines of the email and parse it
        msg_content = b"\r\n".join( lines )
        msg = Parser( ).parsestr( msg_content.decode( "utf-8" ) )

        # Decode the email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance( subject, bytes ):
            subject = subject.decode( encoding if encoding else "utf-8" )

        # Get the sender's email address
        from_ = msg.get( "From" )

        # Get the email body (first few lines)
        body = ""
        if msg.is_multipart( ):
            for part in msg.walk( ):
                content_type = part.get_content_type( )
                content_disposition = str( part.get( "Content-Disposition" ) )
            
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        body = part.get_payload( decode=True ).decode( "utf-8" )
                        break
        else:
            body = msg.get_payload( decode=True ).decode( "utf-8" )

        # Add the subject and first 10 lines to the list
        first_lines = "\n".join( body.splitlines()[:10] )
        emails_info.append( ( from_, subject, first_lines ) )

    # Logout from the POP3 server
    mail.quit()

    # Return the subjects and first few 10 lines of each email
    id = 0
    context = ""
    for from_, subject, first_lines in emails_info:
        context += f"Message #{id}\n"
        context += f"From: {from_}\n"
        context += f"Subject: {subject}\n"
        context += f"{first_lines}\n"
        context += "\n\n"
        id = id + 1

    return context


def Summarize_Email( context ) -> None:

    prompt = \
       """Your role is an email summarizer.  Below you'll find a list of emails. 
       Please provide a short summary of any important emails and ignore any 
       which appear to be spam, advertisements, or not urgent.  You don't need to 
       refer to the messages specifically, but just summarize.  Also report the 
       number of new emails that you founat.\n\n"
       """

    message = prompt + context

    # Get the OPENAI Key
    openai_key = os.environ.get( 'OPENAI_KEY', None )
    if openai_key is None:
        print( "OPENAI_KEY is not set" )
        return

    # Connect to the OpenAI Server
    client = OpenAI(
        api_key = openai_key
    )

    chat_completion = client.chat.completions.create(
        messages = [
            {
                "role": "user",
                "content": message,
            }
        ],
        model="gpt-4o",
    )

    return chat_completion.choices[0].message.content.strip()


def main() -> None:

    context = Get_Email_Context( )

    response = Summarize_Email( context )

    print( response  )


if __name__ == "__main__":
    main()