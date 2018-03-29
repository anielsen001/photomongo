"""
module to allow for sending of gmail notices about status of search results

For documentation go here:
https://developers.google.com/gmail/api/quickstart/python
follow the quickstart.py instructions to configure account access

To create API tokens and access go here:
https://console.developers.google.com

"""

import httplib2
import os

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64


class Gmail(object):
    """
    class to handle connecting to gmail so that emails may be sent
    """
    send_to = None
    send_from = None

    credentials = None
    service = None

    client_secret_file = None
    scopes = None
    application_name = None

    # the google service object that will perform the work
    service = None

    def __init__(self,gmailconf):
        """
        gmailconf should be a dictionary-like object with required keys:
        credential file 
        """
        self.credential_file = gmailconf['credential file']

        self.client_secret_file = gmailconf['client secret file']
        self.scopes = gmailconf['scopes']
        self.application_name = gmailconf['application name']

        self.send_to = gmailconf['to email address']
        self.send_from = gmailconf['from email address']
        
        # get the login credentials from storage, or generate them
        self.credentials = self.get_credentials()

        # create the service object
        http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       self.credential_file)

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file, self.scopes)
            flow.user_agent = self.application_name

            # flags need to be set
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    
    # from:
    # https://developers.google.com/gmail/api/guides/sending
    # the original google code example did not work with python3, hence
    # the mods
    def create_message(self, subject, message_text):
      """Create a message for an email.

      Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.

      Returns:
        An object containing a base64url encoded email object.
      """
      message = MIMEText(message_text)
      message['to'] = self.send_to
      message['from'] = self.send_from
      message['subject'] = subject
      #raw = base64.urlsafe_b64encode(message.as_string().encode('ascii'))
      raw = base64.urlsafe_b64encode(message.as_bytes())
      raw = raw.decode()
      return {'raw': raw }
      #return {'raw': base64.urlsafe_b64encode(message.encode('ascii'))}

    def send_message(self,  message):
      """Send an email message.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

      Returns:
        Sent Message.
      """
      service = self.service
      user_id = 'me'
      
      try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print('Message Id: ' + message['id'])
        return message
      except errors.HttpError:
        print('An error occurred')
        raise

    def create_and_send_message(self,subject,message_text):

        """ combine create and send message methods """

        msg = self.create_message(subject,message_text)
        self.send_message(msg)

        
        
