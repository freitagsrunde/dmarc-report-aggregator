#!/usr/bin/env python3
import email
import sys
from pathlib import Path
from smtplib import SMTP

if __name__ == '__main__':
    for eml_path in sys.argv[1:]:
        with open(eml_path, "rb") as file:
            message = email.message_from_binary_file(file)

        with SMTP("localhost", 8025) as smtp:
            smtp.send_message(message)
