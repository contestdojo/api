from marshmallow import Schema, fields
from marshmallow_union import Union

from contestdojo_api.firebase import db


class DocumentReference(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return value.path

    def _deserialize(self, value, attr, data, **kwargs):
        return db.document(value)


class UserSchema(Schema):
    id = fields.Str()
    email = fields.Str()
    fname = fields.Str()
    lname = fields.Str()
    type = fields.Str()


class OrganizationSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    admin = DocumentReference()
    address = fields.Str()
    city = fields.Str()
    state = fields.Str()
    country = fields.Str()
    zip = fields.Str()
    adminData = fields.Nested(UserSchema)


class EntitySchema(Schema):
    id = fields.Str()
    name = fields.Str()
    admins = fields.List(DocumentReference())
    stripeAccount = fields.Str()


class EventCostAdjustmentRuleSchema(Schema):
    field = fields.Str()
    rule = fields.Str()
    value = fields.Str()


class EventCostAdjustmentSchema(Schema):
    rule = fields.Nested(EventCostAdjustmentRuleSchema)
    adjustment = fields.Number()


class EventCustomFieldFlagsSchema(Schema):
    required = fields.Bool()
    editable = fields.Bool()
    hidden = fields.Bool()


class EventCustomFieldSchema(Schema):
    id = fields.Str()
    label = fields.Str()
    choices = fields.List(fields.Str())
    helpText = fields.Str()
    validationRegex = fields.Str()
    flags = fields.Nested(EventCustomFieldFlagsSchema)


class EventSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    date = fields.DateTime()
    owner = DocumentReference()
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


class EventOrganizationSchema(Schema):
    id = fields.Str()
    maxStudents = fields.Number()
    notes = fields.Str()
    customFields = fields.Dict()
    code = fields.Str()


class EventStudentSchema(Schema):
    id = fields.Str()
    email = fields.Str()
    fname = fields.Str()
    lname = fields.Str()
    grade = Union([fields.Number(), fields.Str()])
    user = DocumentReference()
    org = DocumentReference()
    team = DocumentReference()
    number = fields.Str()
    waiver = Union([fields.Bool(), fields.Str()])
    notes = fields.Str()
    customFields = fields.Dict()


class EventTeamSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    org = DocumentReference()
    number = fields.Str()
    scoreReport = fields.Str()
    notes = fields.Str()
    customFields = fields.Dict()
    code = fields.Str()