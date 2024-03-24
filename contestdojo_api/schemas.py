from marshmallow import Schema, fields
from marshmallow_union import Union

from .firebase import db


class DocumentReference(fields.Field):
    def __init__(self, *args, collection=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._collection = collection

    @property
    def collection(self):
        if callable(self._collection):
            return self._collection(self)
        return self._collection

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if value.parent != self.collection:
            raise ValueError(f"DocumentReference must be in collection {self.collection}")
        return value.id

    def _deserialize(self, value, attr, data, **kwargs):
        return self.collection.document(value)


class FirebaseSchema(Schema):
    def dump_firestore(self, obj):
        return self.dump({"id": obj.id, **obj.to_dict()})


class UserSchema(FirebaseSchema):
    id = fields.Str()
    email = fields.Str()
    fname = fields.Str()
    lname = fields.Str()
    type = fields.Str()


class OrganizationSchema(FirebaseSchema):
    id = fields.Str()
    name = fields.Str()
    admin = DocumentReference(collection=db.users)
    address = fields.Str()
    city = fields.Str()
    state = fields.Str()
    country = fields.Str()
    zip = fields.Str()
    adminData = fields.Nested(UserSchema)


class EntitySchema(FirebaseSchema):
    id = fields.Str()
    name = fields.Str()
    admins = fields.List(DocumentReference(collection=db.users))
    stripeAccount = fields.Str()


class EventCostAdjustmentRuleSchema(FirebaseSchema):
    field = fields.Str()
    rule = fields.Str()
    value = fields.Str()


class EventCostAdjustmentSchema(FirebaseSchema):
    rule = fields.Nested(EventCostAdjustmentRuleSchema)
    adjustment = fields.Number()


class EventCustomFieldFlagsSchema(FirebaseSchema):
    required = fields.Bool()
    editable = fields.Bool()
    hidden = fields.Bool()


class EventCustomFieldSchema(FirebaseSchema):
    id = fields.Str()
    label = fields.Str()
    choices = fields.List(fields.Str())
    helpText = fields.Str()
    validationRegex = fields.Str()
    flags = fields.Nested(EventCustomFieldFlagsSchema)


class EventSchema(FirebaseSchema):
    id = fields.Str()
    name = fields.Str()
    date = fields.DateTime()
    owner = DocumentReference(collection=db.entities)
    frozen = fields.Bool()
    hide = fields.Bool()
    costPerStudent = fields.Number()
    costAdjustments = fields.List(fields.Nested(EventCostAdjustmentSchema))
    studentsPerTeam = fields.Int()
    maxTeams = fields.Int()
    scoreReportsAvailable = fields.Bool()
    description = fields.Str()
    costDescription = fields.Str()
    waiver = Union([fields.Bool(), fields.Str()])
    customFields = fields.List(fields.Nested(EventCustomFieldSchema))
    customOrgFields = fields.List(fields.Nested(EventCustomFieldSchema))
    customTeamFields = fields.List(fields.Nested(EventCustomFieldSchema))
    studentRegistrationEnabled = fields.Bool()


class EventOrganizationSchema(FirebaseSchema):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    maxStudents = fields.Int()
    notes = fields.Str()
    customFields = fields.Dict()
    code = fields.Str(dump_only=True)
    startTime = fields.DateTime()
    updateTime = fields.DateTime()


class EventStudentSchema(FirebaseSchema):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    id = fields.Str(dump_only=True)
    email = fields.Str(dump_only=True)
    fname = fields.Str(dump_only=True)
    lname = fields.Str(dump_only=True)
    grade = Union([fields.Int(), fields.Str()])
    user = DocumentReference(collection=db.users, dump_only=True)
    org = DocumentReference(collection=db.orgs)
    team = DocumentReference(collection=lambda f: db.eventTeams(f.parent.event.id))
    number = fields.Str()
    waiver = Union([fields.Bool(), fields.Str()])
    notes = fields.Str()
    customFields = fields.Dict()
    checkInPool = fields.Str(dump_only=True)


class EventTeamSchema(FirebaseSchema):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    id = fields.Str(dump_only=True)
    name = fields.Str()
    org = DocumentReference(collection=db.orgs)
    number = fields.Str()
    scoreReport = fields.Str(dump_only=True)
    notes = fields.Str()
    customFields = fields.Dict()
    code = fields.Str(dump_only=True)
    checkInPool = fields.Str(dump_only=True)
