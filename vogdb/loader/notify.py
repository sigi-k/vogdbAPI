import smtplib
import os

EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
RECIPIENT = os.environ.get('EMAIL_USER')  # provisional for testing purposes: sender = recipient
# RECIPIENT = 'issue_tracker'  be sure to change the recipient email_address accordingly


def notify():

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()  # encrypted connection
        smtp.starttls()
        smtp.ehlo()

        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        subject = 'VOGDB: INCONSISTENT DATA!'
        body = 'There is an issue with data integrity of VOGDB (Either case 1 or case 2): \n\n\
Case 1: Inconsistencies with md5 checksums at http://fileshare.csb.univie.ac.at/vog/latest/ detected.\n\
Case 2: The number of species, proteins or vogs in the MySQL database does not correspond to the numbers given at https://vogdb.csb.univie.ac.at/reports/release_stats'
        msg = f'Subject: {subject}\n\n{body}'

        # logging.info('Sending Email...')
        smtp.sendmail(EMAIL_ADDRESS, RECIPIENT, msg)


if __name__ == "__main__":
    notify()
