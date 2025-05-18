from app.models.model import Client
import logging

logger = logging.getLogger(__name__)


# Handles all CRUD operations for clients model
class ClientsRepository:
    # Creates a client
    @staticmethod
    async def create_client(
        name: str,
        ai_phone_number: str,
        ai_bot_name: str,
    ):
        try:
            client_instance: Client = await Client.create(
                name=name,
                ai_phone_number=ai_phone_number,
                ai_bot_name=ai_bot_name,
            )
            return client_instance
        except Exception as error:
            print("Unable to create client: ", error)
            logger.error("Unable to create client: ", error)
            raise error

    # Retrieves all clients
    @staticmethod
    async def get_all_clients():
        try:
            clients = await Client.all()
            return clients
        except Exception as error:
            print("Unable to retrieve clients: ", error)
            logger.error("Unable to retrieve clients: ", error)
            raise error

    # Retrieves a client by id
    @staticmethod
    async def get_client_by_id(client_id: str):
        try:
            client = await Client.get(id=client_id)
            return client
        except Exception as error:
            print("Unable to retrieve client: ", error)
            logger.error("Unable to retrieve client id: ", error)
            raise error

    # Retrieves a client by id
    @staticmethod
    async def get_client_by_uuid(client_uuid: str):
        try:
            client = await Client.get(uuid=client_uuid)
            return client
        except Exception as error:
            print("Unable to retrieve client by uuid: ", error)
            logger.error("Unable to retrieve client by uuid: ", error)
            raise error

    # Retrieves a client by id
    @staticmethod
    async def get_client_id_by_uuid(client_uuid: str):
        try:
            client = await Client.get(uuid=client_uuid)
            return client.id
        except Exception as error:
            print("Unable to retrieve client: ", error)
            logger.error("Unable to retrieve client by uuid: ", error)
            raise error

    # Updates a client
    @staticmethod
    async def update_client(client_id: str, name: str):
        try:
            await Client.filter(id=client_id).update(name=name)
        except Exception as error:
            print("Unable to update client: ", error)
            logger.error("Unable to update client: ", error)
            raise error

    # Deletes a client
    @staticmethod
    async def delete_client(client_id: str):
        try:
            await Client.filter(id=client_id).delete()
        except Exception as error:
            print("Unable to delete client: ", error)
            logger.error("Unable to delete client: ", error)
            raise error

    @staticmethod
    async def get_client_id_by_phone_number(ai_phone_number: str):
        try:
            client = await Client.filter(ai_phone_number=ai_phone_number).get()
            return client.id
        except Exception as error:
            print("Unable to retrieve client by phone number: ", error)
            logger.error("Unable to retrieve client by phone number: ", error)
            raise error
