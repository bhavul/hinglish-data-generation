# hinglish-data-generation


This is a try at generating a big dataset of hinglish, which currently does not exist.
The repo has come up as a way for me to learn Kafka and is initially inspired from the following blog : 

https://florimond.dev/blog/articles/2018/09/building-a-streaming-fraud-detection-system-with-kafka-and-python/

http://docs.tweepy.org/en/v3.4.0/streaming_how_to.html

# How to start?

Do note that to run this you first need a Twitter Developer account and set up an App there and get the credentials. These credentials then go in a `.env` file (check `.env.example`). 

```
# 1. Start kafka & zookeeper
docker-compose -f docker-compose.kafka.yml up -d

# 2. Start tweets producer and consumer service
docker-compose up -d
```

Currently the producer runs only for 10 minutes and then exits. You can easily remove this time limit (by commenting `PRODUCER_TIME_LIMIT` flag in your `.env`). In initial testing, this generates close to 30-60 hinglish tweets within 5 minutes. 
 

## Check logs

For kafka...  

`docker-compose -f docker-compose.kafka.yml logs broker`  

To check kafka queues :   

`docker-compose -f docker-compose.kafka.yml exec broker kafka-console-consumer --bootstrap-server localhost:9092 --topic queueing.tweets --from-beginning
`  

For tweet producer :   

`docker-compose logs tweets-producer`

For tweet consumer :   

`docker-compose logs hinglish-consumer`


# What we're doing here

We use Tweepy client to use Twitter Streaming API and stream tweets. These are all kinds of tweets belonging to any language. These tweets go into Kafka queue/topic (named `queuing.tweets`). Then a consumer processes them to put the ones which are hinglish tweets in a file.

Twitter Streaming API allows you to get tweets either based on search keywords OR to get a 1% sample of tweets. The former has a limitation of 400 search keywords and just 500,000 tweets a month for a non-enterprise Twitter Developer account. The latter does not have this limitation.

For this reason we're using streaming sample API of twitter - which usually gives us a lot of junk and only one or two hinglish tweets in every 1000 tweets that get put into the queue/topic. 


## Upcoming features (tentative)

1. Basic system to put new hinglish tweets in some DB instead of a file.
2. Better classification system for consumer to only store cleaned and good tweets.
3. Separation of producer and consumer to do independent scaling
4. Trying to setup Kafka cluster instead of single kafka 
5. Storing UserIds which regularly tweet in hinglish.
6. Store hashtags as they could be useful for topic modelling
7. Clean emojis
8. Add elasticsearch into the mix for searching tweets with keywords
9. Add some NoSQL db into the mix.


# Want to Contribute

Currently the project is in infancy stage. It would take couple of weeks to get to a decent state from aspects of what it does, how it does and the documentation. If you still wish to get started on this sooner, the codebase is small enough to be understood in an hour or so. So go ahead! :) 