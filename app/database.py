import mongoengine
import json
import os
import logging

mongoengine.connect(
    os.environ['MONGODB_DATABASE'],
    host=os.environ['MONGODB_HOSTNAME'],
    username=os.environ['MONGODB_USERNAME'],
    password=os.environ['MONGODB_PASSWORD'],
    port=27017,
    authentication_source='admin')

#mongoengine.connect(os.environ['MONGODB_DATABASE'], host=f"mongodb://{os.environ['MONGODB_USERNAME']}:{os.environ['MONGODB_PASSWORD']}@{os.environ['MONGODB_HOSTNAME']}:27017/{os.environ['MONGODB_DATABASE']}?authSource=dbWithUserCredentials")

# username=os.environ['MONGODB_USERNAME'],
# password=os.environ['MONGODB_PASSWORD'],
# authentication_source='admin')


class User(mongoengine.Document):
    _id = mongoengine.StringField(required=True, primary_key=True)
    username = mongoengine.StringField(default='None')
    name = mongoengine.StringField(required=True)
    phone_number = mongoengine.StringField(required=True)


async def create_db():
    if User.objects().first():
        logging.info(f"{os.environ['MONGODB_DATABASE']} database has already been created")
    else:
        try:
            User(_id='242212223',
                 name='Admin',
                 phone_number='0683358425').save()
            logging.info(f"Successful create {os.environ['MONGODB_DATABASE']} database ")
        except Exception as e:
            logging.error(f"Failed create {os.environ['MONGODB_DATABASE']} database")
