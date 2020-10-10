# Learnings

The entire project was done to learn to deal with Kafka and Docker and a bunch of different services I haven't had the chance to work with. 

So it's important to note down all learnings.

## Design

- Usually in Kafka based systems even if producer and consumer apps are coupled on same system, the Kafka service is kept separate. This allows you to have a Kafka cluster which is separate
- If your consumer is going to write data in a file, better to do in batches. Less reads to disk means better efficiency.


## Kafka

- python client to use `kafka-python` - contains both consumer and producer code
- When you're writing to a topic you need to write bytes. So you need to use `.encode()` 
    - You could also use a `value_serializer` which could be a lambda method directly while instantiating `KafkaProducer`.
- Kafka runs with help of Zookeeper. So by default Kafka itself requires two services - Kafka and Zookeeper. Hence it has its own docker-compose file.
- Most of Kafka docs I am learning from official docs and have highlighted it [there only](https://kafka.apache.org/documentation/).
- The consumer works on a pull based methodology. So it tries to keep pulling from topic by polling it. Hence once you define a `KafkaConsumer` you don't need to put your code in a `while True` loop. That stuff is taken care of by `KafkaConsumer` itself. You can have a simple loop assuming you're getting messages in `consumer` object (of type `KafkaConsumer`) and just do your stuff
- If you need to interact with the message - the actual message is in `message.value`. You should also first decode it. So if it's a simple string you get actual message by `message.value.decode('utf-8')`.

## Tweepy & Twitter

- The twitter dev account credentials activate immediately. 
- By default you can do two kinds of streaming : 
    - ***sample streaming*** which gives you 1% of current tweets from entire world with only language filter available
    - ***filter stream*** which lets you get streaming tweets containing keywords, or location you specify.
- Filter streaming API has a limit of 500,000 tweets in a month which is pretty less
- Sample streaming API does not count towards your API usage so you can practically keep getting new tweets without any limit
- There are two kinds of authentication - OAuth1.1 and OAuth2. Twitter suggests to use OAuth2 and Tweepy supports it but in OAuth2 streaming fails silently. You need to use OAuth1 even though all you're doing is reading.
- There's no way to stop the streaming unless / until you `return False` from `on_status` or `on_data` method in your StreamListener class
- When you select language as `en` for streaming.sample() it somehow doesn't return any hinglish tweets at all. Twitter probably understands something is code-mixed and doesn't throw that into the `en` language filter.


## Docker

- For each of your service you need to first have its own simple Dockerfile which just copies the code, installs the requirements and can run the app
- For a python app when you put `CMD ['python', 'app.py']` it doesn't output logs to STDOUT. You need to use `CMD ['python','-u','app.py']` so it flushes whatever IO related stuff it needs to do. This fixes the problem.


## Docker-compose

- You need to keep `version` key at the top of the file and it must be 3 (or above). This is not version of your software but rather defining type/structure of your docker-compose file.
- You can have multiple `docker-compose.xml` files for services which you would want to be kept de-coupled. So that if need be you can scale/kill/modify one independently
- When you do keep different services spawned up you need to have an **external network** defined on which these can communicate:
    - For this first create a new docker network : `docker network create kafka-network`
    - Then in each of the `docker-compose.X.xml` files add the following : 
    ```
        # Give this composition access to the Kafka network
    networks:
      default:
        external:
          name: kafka-network
    ```
- Define all your config via **environment variables** in `docker-compose.xml` and let your `app.py` of each service read the environment variables for configs. This is done with `environment:` key in the `docker-compose.xml` file.
- Usually the mounted places in the container lie inside `/tmp/XYZ` dir or `/var/lib/XYZ` dir. Not sure why but that seems to be the convention.
- The volumes aspect needs to come in `docker-compose.xml` and not in the actual Dockerfile.
- For each of your services as long as they have their own folders and contain a file named `Dockerfile` inside them you can just define the folder path in `build:` key in docker-compose file.
- In `volumes:` you can give host's relative path. This is always relative to the docker-compose.xml file.
- For any kind of secrets don't expose them in `docker-compose.xml` directly as environment config variables. Rather use **docker secrets**. [More here](https://medium.com/lucjuggery/from-env-variables-to-docker-secrets-bc8802cacdfd). However this requires your docker containers to not be container but rather docker services and run in a swarm which can then be scaled. Secrets are automatically then given to containers in a swarm.
- A simpler way is you can keep a `.env` file which can be added to `.gitignore` and can be different in your prod versus dev environments. Here you can define your secrets. This way your secrets dont get exposed in Git repo.
