import os
import json
import smtplib
from email.mime.text import MIMEText
from confluent_kafka import Consumer, KafkaError
##################
from dotenv import load_dotenv
load_dotenv()


KAFKA_CONF = {
    'bootstrap.servers': os.environ.get('KAFKA_SERVERS', 'localhost:9092'),
    'group.id': 'crm-group',
    'auto.offset.reset': 'earliest'
}
KAFKA_TOPIC = "linyul.customer.evt" 
ANDREW_ID = "linyul"

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')

def send_email(customer_name, customer_email):
    subject = "Activate your book store account"
    body = f"""Dear {customer_name},
Welcome to the Book store created by {ANDREW_ID}.
Exceptionally this time we won't ask you to click a link to activate your account."""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = customer_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"Successfully sent email to {customer_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([KAFKA_TOPIC])
    print(f"CRM Service started. Listening to {KAFKA_TOPIC}...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF: continue
                else: print(msg.error()); break

            try:
                data = json.loads(msg.value().decode('utf-8'))
                customer_name = data.get('name')
                customer_email = data.get('userId')
                
                if customer_name and customer_email:
                    send_email(customer_name, customer_email)
            except Exception as e:
                print(f"Error processing message: {e}")
                
    finally:
        consumer.close()

if __name__ == "__main__":
    main()