# detector/app.py
import os
import re
import csv
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
TWEETS_QUEUE_TOPIC = os.environ.get("TWEETS_QUEUE_TOPIC")
PATH_DB_FILE = os.environ.get("DB_FILE")
CLOSE_MESSAGE = os.environ.get("SPECIAL_CLOSE_FLAG")


class PreProcessor:

    def __init__(self, message):
        self.message = message
        self.hashtags = []

    def replace_line_breaks(self):
        self.message.replace('\n', '<br>')
        return self

    def remove_urls(self):
        self.message = re.sub(r'http\S+', '', self.message)
        return self

    def remove_mentions(self):
        self.message = re.sub(r"(?:\@|https?\://)\S+", "", self.message)
        return self

    def extract_hashtags(self):
        self.hashtags = re.findall(r"#(\w+)", self.message)
        self.message = re.sub(r"#(\w+)", '', self.message)
        return self


def is_retweet(message) -> bool:
    if 'RT' in message:
        return True
    else:
        return False


# todo : separate out as a LanguageDetector module
def is_hinglish(message) -> bool:
    message = message.lower()
    words_list = message.split()
    common_hinglish_words = ["kyun", "karta", "tum", "nahi", "kabhi", "sakta", "sakti", "kaise", "abhi", "dekhna",
                             "karna", "agar", "thoda", "thodi", "hota", "hone", "dega", "degi", "bhi", "kuch",
                             "kuchh", "mujhe", "bahut", "logon", "karega", "karegi", "wala", "wali", "uske", "unke",
                             "kahin", "mein", "aana", "aane", "aani", "matlab", "hun", "nahin", "hoon", "hun", "agar",
                             "aapke", "tumhare", "tumhari", "tumhara", "bata", "bhai", "behen", "hain"]
    return any(word in words_list for word in common_hinglish_words)


def create_out_file_if_not_exists():
    if not os.path.isfile(PATH_DB_FILE):
        with open(PATH_DB_FILE, 'a') as f:
            cw = csv.writer(f, delimiter=',')
            cw.writerow(['tweet', 'hashtags'])


def is_close_message(message_text):
    return message_text == CLOSE_MESSAGE


if __name__ == "__main__":

    create_out_file_if_not_exists()

    consumer = KafkaConsumer(
        TWEETS_QUEUE_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL
    )

    tweet_count = 0
    # we will save in buffer and do batch writes to disk as that would give better performance
    batch_size = 5
    row_list = []
    for message in consumer:
        tweet_count += 1
        message_text = message.value.decode('utf-8')
        if is_close_message(message_text):
            print('Receieved special exiting message. Will exit now!')
            consumer.close()
            break

        pre_processor = PreProcessor(
            message_text).replace_line_breaks().remove_urls().remove_mentions().extract_hashtags()
        pre_processed_message = pre_processor.message
        hashtags = pre_processor.hashtags  # todo : save this too?
        pre_processed_message = pre_processed_message.strip()

        if pre_processed_message and not is_retweet(pre_processed_message) and is_hinglish(pre_processed_message):
            row_list.append([pre_processed_message, '|'.join(hashtags)])
            print(f'Found hinglish tweet! Tweet #{tweet_count}')
            if len(row_list) >= batch_size:
                print(f'Appending to File!')
                with open(PATH_DB_FILE, 'a') as f:
                    cw = csv.writer(f, delimiter=',')
                    cw.writerows(row_list)
                    row_list = []
