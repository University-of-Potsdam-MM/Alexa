import json
from tincan import (
    RemoteLRS,
    Statement,
    Agent,
    Verb,
    Activity,
    Context,
    Score,
    Result,
    Extensions,
    LanguageMap,
    ActivityDefinition,
)


class LRSClient:

    # config LRS endpoint and auth info here
    LRS = RemoteLRS(
        version="1.0.1",
        endpoint="http://localhost/learninglocker/public/data/xAPI/",
        username="ecd7a4c6658238406835367b65682c73bf5432de",
        password="d47ca3dced71146503033e8d92e2c620b28fbb5e"
    )

    verbs = {
        "selected": "http://id.tincanapi.com/verb/selected",
        "access": "http://activitystrea.ms/schema/1.0/access",
        "experienced": "http://adlnet.gov/expapi/verbs/experienced",
        "listen": "http://activitystrea.ms/schema/1.0/listen",
        "answered": "http://adlnet.gov/expapi/verbs/answered",
        "requested": "https://w3id.org/xapi/adb/verbs/requested",
        "logged-in": "https://w3id.org/xapi/adl/verbs/logged-in",
        "logged-out": "https://w3id.org/xapi/adl/verbs/logged-out",
        "create": "http://activitystrea.ms/schema/1.0/create",
        "delete": "http://activitystrea.ms/schema/1.0/delete",
        "update": "http://activitystrea.ms/schema/1.0/update",
        "completed": "http://adlnet.gov/expapi/verbs/completed",
        "consume": "http://activitystrea.ms/schema/1.0/consume",
        "earned": "http://id.tincanapi.com/verb/earned",
        "passed": "http://adlnet.gov/expapi/verbs/passed",
        "failed": "http://adlnet.gov/expapi/verbs/failed",
        "launched": "http://adlnet.gov/expapi/verbs/launched",
        "start": "http://activitystrea.ms/schema/1.0/start",
        "leave": "http://activitystrea.ms/schema/1.0/leave",
        "paused": "http://id.tincanapi.com/verb/paused",
        "resumed": "http://adlnet.gov/expapi/verbs/resumed",
        "terminated": "http://adlnet.gov/expapi/verbs/terminated"
    }

    objects = {
        "resource": "http://id.tincanapi.com/activitytype/resource"
    }

    extensions = {
        "topic": "http://id.tincanapi.com/extension/topic",
        "interaction": "http://id.tincanapi.com/extension/interaction",
        "difficulty": "http://id.tincanapi.com/extension/difficulty",
        "feedback": "http://id.tincanapi.com/extension/feedback"
    }

    def sendStatement(self, reqData):
        #load requested data for statement generation
        data = json.loads(reqData)

        # create RemoteLRS endpoint
        lrs = self.LRS

        # generate statement

        # 1. actor
        actor = Agent(
            name=data["name"],
            mbox='mailto:' + data["name"] + '@id.lrs',
        )

        # 2. verb
        verb = Verb(
            id=self.verbs.get(data["verb"]),
            display=LanguageMap({'en-US': data["verb"]}),
        )

        # 3. object
        obj = Activity(
            id=self.objects.get(data["activity"]),
            definition=ActivityDefinition(
                name=LanguageMap({'en-US': data["activityid"]})
            )
        )

        # 4. context
        context = Context(
            extensions=Extensions({
                self.extensions.get("difficulty"): data["difficulty"],
                self.extensions.get("interaction"): data["interaction"],
                self.extensions.get("topic"): data["topic"]
            })
        )

        # 5. result
        result = Result(
            score=Score(
                raw=data["score"]
            ),
            success=data["success"]
        )

        # build statement
        statement = Statement(
            actor=actor,
            verb=verb,
            object=obj,
            context=context,
            result=result
        )

        # save statement
        response = lrs.save_statement(statement)

        # check response
        if not response:
            raise ValueError("statement failed to save")
        return str(True)

    # returns statements of an user
    def getStatements(self, name):

        # connect LRS
        lrs = self.LRS

        # specify user as agent
        actor = Agent(
            name=name,
            mbox='mailto:' + name + '@id.lrs',
        )

        # optional specify verb
        verb = Verb(
            id=self.verbs.get("experienced"),
            display=LanguageMap({'en-US': 'experienced'}),
        )

        query = {
            "agent": actor,
            #"verb": verb,
            "limit": 1000 #change limit if needed
        }

        # query LRS for statements
        response = lrs.query_statements(query)

        # check response
        if not response:
            raise ValueError("statements could not be queried")

        # return queried statements
        return response
