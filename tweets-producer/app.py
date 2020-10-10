import os
from kafka import KafkaProducer
import tweepy
import time

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
TWEETS_QUEUE_TOPIC = os.environ.get("TWEETS_QUEUE_TOPIC")
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_AUTH_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_AUTH_CONSUMER_SECRET")
TWITTER_AUTH_ACCESS_TOKEN = os.environ.get("TWITTER_AUTH_ACCESS_TOKEN")
TWITTER_AUTH_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_AUTH_ACCESS_TOKEN_SECRET")
TIME_LIMIT_FOR_PRODUCER = os.environ.get("PRODUCER_TIME_LIMIT")
CLOSE_MESSAGE = os.environ.get("SPECIAL_CLOSE_FLAG")
count_tweets = 0


# override tweepy.StreamListener to add logic to on_status
class MyTwitterStreamListener(tweepy.StreamListener):

    def __init__(self, time_limit=None):
        self.start_time = time.time()
        self.limit = int(time_limit) if time_limit else None
        super().__init__()

    def on_status(self, status):
        global count_tweets
        # print(status.text)
        if self.limit:
            if (time.time() - self.start_time) < self.limit:
                producer.send(TWEETS_QUEUE_TOPIC, value=status.text.encode())
                return True
            else:
                producer.send(TWEETS_QUEUE_TOPIC, value=CLOSE_MESSAGE.encode())
                print(f'Time limit done, exiting streaming!')
                return False
        else:
            # endlessly keep producing
            producer.send(TWEETS_QUEUE_TOPIC, value=status.text.encode())
            return True


    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_error disconnects the stream
            print(f'ERROR : 420...')
            return False

        # returning non-False reconnects the stream, with backoff.


if __name__ == "__main__":
    # initialise kafka producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URL
    )
    # authorizer twitter (OAuthv1) If we use OAuth2 -- streaming doesn't work apparently
    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_AUTH_ACCESS_TOKEN, TWITTER_AUTH_ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth, wait_on_rate_limit=False,
                     wait_on_rate_limit_notify=True)

    # initialise twitter stream connection
    myStreamListener = MyTwitterStreamListener(time_limit=TIME_LIMIT_FOR_PRODUCER)

    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    # starting a stream
    # todo - add filter based fetching (limit of 200,000 tweets per month though) so need to be cautious.
    # myStream.filter(track=['hai', 'haan', 'kyun', 'karta', 'hota', 'nahi', 'main', 'tum', 'kaun', 'kaise', 'kabhi', 'koi'])
    myStream.sample()
