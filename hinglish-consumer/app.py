# detector/app.py
import os
import re
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
TWEETS_QUEUE_TOPIC = os.environ.get("TWEETS_QUEUE_TOPIC")
PATH_DB_FILE = os.environ.get("DB_FILE")


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
    common_hinglish_words = ("kyun", "karta", "tum", "nahi", "kabhi")
    return any(word in message for word in common_hinglish_words)


if __name__ == "__main__":
    consumer = KafkaConsumer(
        TWEETS_QUEUE_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL
    )

    tweet_count = 0
    # we will save in buffer and do batch writes to disk as that would give better performance
    msg_buffer = []
    batch_size = 5
    for message in consumer:
        tweet_count += 1
        pre_processor = PreProcessor(
            message.value.decode("utf-8")).replace_line_breaks().remove_urls().remove_mentions().extract_hashtags()
        pre_processed_message = pre_processor.message
        hashtags = pre_processor.hashtags  # todo : save this too?
        pre_processed_message = pre_processed_message.strip()

        if pre_processed_message and not is_retweet(pre_processed_message) and is_hinglish(pre_processed_message):
            print(f'Found hinglish tweet! Tweet #{tweet_count}')
            msg_buffer.append(pre_processed_message)
            if len(msg_buffer) >= batch_size:
                print(f'Appending to File!')
                with open(PATH_DB_FILE, 'a') as f:
                    f.writelines(msg_buffer)
                msg_buffer = []
