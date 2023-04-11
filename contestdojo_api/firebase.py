import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import firestore_async as firebase_firestore_async
from google.cloud.firestore import AsyncClient

from contestdojo_api import settings

__all__ = (
    "app",
    "auth",
    "firestore",
    "db",
)


class Database:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    def document(self, *path: str):
        return self.client.document(*path)

    @property
    def users(self):
        return self.client.collection("users")

    @property
    def orgs(self):
        return self.client.collection("orgs")

    @property
    def entities(self):
        return self.client.collection("entities")

    @property
    def events(self):
        return self.client.collection("events")

    def eventOrgs(self, eventId: str):
        return self.events.document(eventId).collection("orgs")

    def eventStudents(self, eventId: str):
        return self.events.document(eventId).collection("students")

    def eventTeams(self, eventId: str):
        return self.events.document(eventId).collection("teams")

    def user(self, id: str):
        return self.users.document(id)

    def org(self, id: str):
        return self.orgs.document(id)

    def entity(self, id: str):
        return self.entities.document(id)

    def event(self, id: str):
        return self.events.document(id)

    def eventOrg(self, eventId: str, id: str):
        return self.eventOrgs(eventId).document(id)

    def eventStudent(self, eventId: str, id: str):
        return self.eventStudents(eventId).document(id)

    def eventTeam(self, eventId: str, id: str):
        return self.eventTeams(eventId).document(id)


cred = credentials.Certificate(settings.FIREBASE_CERTIFICATE)
app = firebase_admin.initialize_app(cred)
auth = firebase_auth.Client(app)
firestore = firebase_firestore_async.client(app)
db = Database(firestore)
