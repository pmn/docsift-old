from datetime import datetime
from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

import math
import settings

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
db = SQLAlchemy(app)

class ActionLog(db.Model):
    """ 
    Logging for activities on the site.
    """
    id = db.Column(db.Integer, primary_key=True)
    log_time = db.Column(db.DateTime)
    log_source = db.Column(db.String(100))
    log_message = db.Column(db.String(2000))

    def __init__(self, source, message):
        self.log_time = datetime.utcnow()
        self.log_source = source
        self.log_message = message

    def __repr__(self):
        return "<Event: %s in %s at %s>" % (self.log_message, self.log_source, self.log_message)

class Campaign(db.Model):
    """
    The categorization campaign.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    question = db.Column(db.String(500))
    options = db.relationship("CampaignOption")
    terms = db.relationship("CampaignTerm")
    answers = db.relationship("CampaignAnswer")
    reward_per_quiz = db.Column(db.Numeric)
    terms_per_quiz = db.Column(db.Integer)
    times_per_term = db.Column(db.Integer)
    job_generated = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime)
    
    def cost(self):
        """
        Calculate how much a campaign will cost
        """
        numquizzes = math.ceil(
            (len(self.terms) * self.times_per_term) / float(self.terms_per_quiz))
        cost = float(numquizzes) * float(self.reward_per_quiz)
        return cost

    def get_results(self):
        """
        Used to display campaign results on the details page.
        """
        results = []
        for term in self.terms:
            result = [ResultItem(option.id,
                                 option.option_text,
                                 CampaignAnswer.query.filter_by(option_id = option.id,
                                                              term_id = term.id).count(),
                                 self.times_per_term) for option in self.options]
            results.append(CampaignResult(term.id, term.term, result))
        return results

    def get_result_dump(self):
        """ 
        Use this to get a raw-ish dump of the results.
        """
        results = []
        answered_times = 0
        chosen_answer = ""
        for term in self.terms:
            answers = dict([(option.option_text,
                            CampaignAnswer.query.filter_by(option_id = option.id,
                                                           term_id = term.id).count())
                            for option in self.options])
            bestanswer = max(answers, key=answers.get)
            bestanswer_count = answers[bestanswer]
            bestanswer_percent = (bestanswer_count / float(self.times_per_term) * 100)

            if bestanswer_percent < settings.THRESHOLD:
                # If the required threshold hasn't been met, there is no real best answer
                bestanswer = ""

            result = [term.term, bestanswer,  answers]
            results.append(result)

        return results

    def __init__(self, title, question, terms_per_quiz=None, reward_per_quiz=None, 
                 times_per_term=None, created_date=None):
        self.title = title
        self.question = question
        self.reward_per_quiz = reward_per_quiz
        self.terms_per_quiz = terms_per_quiz
        self.times_per_term = times_per_term
        if created_date is None:
            self.created_date = datetime.utcnow()

    def __repr__(self):
        return '<Campaign %r>' % self.title

class CampaignOption(db.Model):
    """
    Represents the question displayed to the answerer: e.g. "Is this item a vegetable?"
    """
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(500))

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    campaign = db.relationship('Campaign', 
                               backref=db.backref('campaign_option', lazy='dynamic'))

    answers = db.relationship('CampaignAnswer')
    
    def __init__(self, campaign, option_text):
        self.campaign = campaign
        self.option_text = option_text

class CampaignTerm(db.Model):
    """
    The term being categorized.
    """
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100))

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    campaign = db.relationship('Campaign', 
                               backref=db.backref('campaign_term', lazy='dynamic'))

    answers = db.relationship("CampaignAnswer")

    def __init__(self, campaign, term):
        self.campaign = campaign
        self.term = term

class CampaignAnswer(db.Model):
    """
    The answerer's categorization of the term. 
    There will be many of these for each term.
    """
    id = db.Column(db.Integer, primary_key=True)
    hit = db.Column(db.String(50))
    worker = db.Column(db.String(50))

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    term_id = db.Column(db.Integer, db.ForeignKey('campaign_term.id'))
    option_id = db.Column(db.Integer, db.ForeignKey('campaign_option.id'))

    campaign = db.relationship('Campaign',
                               backref=db.backref('campaign_answer'))

    term = db.relationship('CampaignTerm', 
                           backref=db.backref('campaign_answer'))
  
    option = db.relationship('CampaignOption',
                             backref=db.backref('campaign_answer'))

    def __init__(self, hit, worker, campaign_id, term_id, option_id):
        self.hit = hit
        self.worker = worker
        self.campaign_id = campaign_id
        self.term_id = term_id
        self.option_id = option_id
    
    def __repr__(self):
        return "<Answer: '%s - %s'>" % (self.term.term, self.option.option_text)

class ResultItem():
    """
    A non-database class used for reporting campaign results.
    """
    def __init__(self, option_id, option_text, times_selected, total_selections):
        self.option_id = option_id
        self.option_text = option_text
        self.times_selected = times_selected
        self.total_selections = total_selections
        self.percentage = int((times_selected / float(total_selections)) * 100)
        
    def __repr__(self):
        return "<Result: %s, %s%%>" % (self.answer, self.percentage)

class CampaignResult():
    """
    A non-database class used for reporting campaign results.
    """
    def answer_breakdown(self):
        """
        Create a breakdown of answer selections for use in the 
        summary view of the campaign.
        """
        out = ""
        for result in self.results:
            out += "%s: %s%% " % (result.option_text, result.percentage)
        return out

    def is_inconclusive(self, threshold=settings.THRESHOLD):
        """
        Return True if the result is inconclusive, otherwise return False.
        """
        print "testing conclusiveness"
        inconclusive = True
        for result in self.results:
            if result.percentage > threshold:
                inconclusive = False
        return inconclusive

    def choose_answer(self, threshold=settings.THRESHOLD):
        """
        Select the most frequently chosen answer.
        """
        answer = ResultItem(-1, "Inconclusive",0,1)
        for result in self.results:
            if (result.percentage > answer.percentage) and (result.percentage > threshold):
                answer = result
        return answer

    def __init__(self, termid, term, result_items):
        self.termid = termid
        self.term = term
        self.results = result_items
        self.answer = self.choose_answer()
    
    def __repr__(self):
        answer = self.choose_answer()
        return (self.term, answer.answer_text, answer.percentage)


