import logging
import smtplib
import argparse

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from selenium import webdriver
from selenium.webdriver.common.by import By

def main():
    parser = argparse.ArgumentParser(description='A simple notification bot for Slightly Toasted events', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--verbose', action='store_const', const=logging.DEBUG, default=logging.INFO, help='enable debug logging')
    parser.add_argument('--unattended', action='store_true', help='configure the script to run unattended')
    parser.add_argument('--data_store', default='previous-events.txt', type=argparse.FileType('a+'), help='flat file data store')

    selenium_settings = parser.add_argument_group('Selenium Settings', description='configuration settings for running selenium')
    selenium_settings.add_argument('--firefox_driver', default='/snap/bin/geckodriver', help='path to gecko driver for firefox')

    aws_ses_settings = parser.add_argument_group('AWS SES Settings', description='settings for Amazon SES when sending notification emails')
    aws_ses_settings.add_argument('-u', dest='username', required=True)
    aws_ses_settings.add_argument('-p', dest='password', required=True)
    aws_ses_settings.add_argument('-s', dest='sender', required=True)
    aws_ses_settings.add_argument('-r', dest='recipient', required=True)
    aws_ses_settings.add_argument('--smtp_endpoint', default='email-smtp.us-east-2.amazonaws.com', help='-')
    aws_ses_settings.add_argument('--smtp_port', default=587, help='-')

    args = parser.parse_args()

    # setup logging
    if args.unattended:
        logging.basicConfig(format='%(asctime)s | %(levelname)s:%(name)s | %(message)s', level=args.verbose, filename='st-event-notifications.log')
    else:
        logging.basicConfig(format='%(asctime)s | %(levelname)s:%(name)s | %(message)s', level=args.verbose)

    # options for the headless selenium driver
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    service = webdriver.FirefoxService(executable_path=args.firefox_driver)

    email_message = ''
    args.data_store.seek(0)
    previous_events = args.data_store.read().splitlines()
    execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    logging.info('--- STARTING SCRIPT ---')

    # process the webpage
    with webdriver.Firefox(options=options, service=service) as driver:
        try:
            driver.get('https://www.exploretock.com/slightlytoasted')
            events_panel = driver.find_elements(By.ID, 'events-panel')

            # process events if they are present
            if len(events_panel) > 0:
                events = events_panel[0].find_elements(By.CLASS_NAME, 'Consumer-reservation')

                for event in events:
                    event_name = event.find_element(By.CLASS_NAME, 'Consumer-reservationHeading').text

                    # if the event has been seen and notified on before, skip it
                    if event_name in previous_events:
                        logging.info(f'Skipping: {event_name}')
                        continue

                    # get the number remaining tickets if any
                    reservation_hints = event.find_elements(By.CLASS_NAME, 'Consumer-reservationHint')

                    # if no tickets remain skip the event
                    # do not mark the event as processed as new tickets may be available at a future time
                    if len(reservation_hints) == 0:
                        logging.info(f'No Tickets Remaining for {event_name}, Skipping')
                        continue

                    logging.info(f'Found: {event_name}')

                    email_message += f'{event_name}\n'

                    remaining_tickets = reservation_hints[0].find_element(By.TAG_NAME, 'span').text
                    email_message += f'* {remaining_tickets}\n'

                    # get event details
                    event_details = event.find_element(By.CLASS_NAME, 'Consumer-reservationMetaList').find_elements(By.TAG_NAME, 'li')

                    for event_detail in event_details:
                        email_message += f'* {event_detail.text}\n'

                    email_message += '\n\n'

                    # store the event name to a data store for state tracking
                    args.data_store.write(f'{execution_time}\n')
                    args.data_store.write(f'{event_name}\n')
            else:
                logging.info('No Events Found')
        except Exception as e:
            logging.error(e)
        finally:
            driver.close()

    # send an email notification if available
    if email_message != '':
        logging.debug(f'Sending Email Message: {email_message}')

        # create the email message
        message = MIMEMultipart()
        message['Subject'] = 'Slightly Toasted Event Notification'
        message['From'] = args.sender
        message.attach(MIMEText(email_message, 'plain'))

        try:
            # connect to the endpoint
            server = smtplib.SMTP(args.smtp_endpoint, args.smtp_port)
            server.starttls()

            # authenticate to the endpoint
            server.login(args.username, args.password)

            # send the email
            server.sendmail(args.sender, args.recipient, message.as_string())

            logging.info(f'Email Sent to {args.recipient}')
        except Exception as e:
            logging.error(e)
        finally:
            server.quit()

if __name__ == '__main__':
    main()