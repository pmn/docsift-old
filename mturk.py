# API for working with Amazon Mechanical Turk
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import QuestionContent, Question, QuestionForm, Overview, AnswerSpecification, SelectionAnswer

from models import db, Campaign, CampaignOption, CampaignTerm, CampaignAnswer
import settings
import math

### HIT Creation ###
def create_connection():
    """ 
    Create a connection to the Mechanical Turk service 
    """
    mtc = MTurkConnection(aws_access_key_id=settings.AWS_ACCESS_ID,
                      aws_secret_access_key=settings.AWS_SECRET_KEY,
                      host=settings.TURK_TEST_HOST)
    return mtc

def build_answers(answerlist):
    """
    Build up the answer selection list from the list of tuples <answerlist>
    """
    answers = SelectionAnswer(min=1,
                              max=1,
                              style='radiobutton',
                              selections=answerlist,
                              type='text',
                              other=False)
    return answers

def create_question_form(title, description, keywords):
    """ 
    Create an overview for an MTurk HIT 
    """
    overview = Overview()
    overview.append_field('Title', title)
    question_form = QuestionForm() 
    question_form.append(overview)
    return question_form

def create_question(identifier, quizquestion, answers):
    """
    Create a question
    """
    newquestion = QuestionContent()
    newquestion.append_field('Title', quizquestion)
    question = Question(identifier=identifier,
                        content=newquestion,
                        answer_spec=AnswerSpecification(build_answers(answers)),
                        is_required=True)
    return question
    
def create_campaign_hits(campaignid):
    """ 
    Create HITs for a campaign. 
    """
    campaign = Campaign.query.filter_by(id=campaignid).first()
    options = campaign.options
    terms = campaign.terms
    
    # Determine the number of quizzes that need to be generated
    numquizzes = int(math.ceil(float(len(terms)) / campaign.terms_per_quiz))

    # A set of questions will be built for each "page"
    for pagenum in range(numquizzes):
        conn = create_connection()
        question_form = create_question_form(campaign.title, campaign.title,"categorization")

        # Add the term questions to the page / quiz
        for i in range(campaign.terms_per_quiz):
            termnum = i + (pagenum * campaign.terms_per_quiz)
            if termnum < len(terms):
                term = terms[termnum]
                # Build up an answer dictionary for use with the question form 
                answers = [(option.option_text, option.id) for option in options]
                # A question should be appended for each term under consideration
                questiontext = campaign.question.replace("[term]", term.term)
                identifier = "%s|%s" % (campaign.id, term.id)
                question_form.append(create_question(identifier,
                                                     questiontext,
                                                     answers))
  
        # Now that the questions have been added, create the HIT
        conn.create_hit(questions=question_form,
                        max_assignments=campaign.times_per_term,
                        title=campaign.title,
                        description=campaign.title,
                        duration=60*5, # allot 5 minutes per quiz 
                        reward=campaign.reward_per_quiz)

    # Update the campaign to prevent multiple generation attempts
    campaign.job_generated = True
    db.session.add(campaign)
    db.session.commit()

### HIT Review & Approval ###
def retrieve_reviewable_hits():
    """
    Get completed HITs from Mechanical Turk. 

    MTurk will only return HITs if all the assignments have
    been completed for a HIT, so there will be no returns
    if 6 assignments out of 10 have been completed, for example.
    """
    # Need to report back whether or not results were returned 
    results_returned = False

    # Create connection to MTurk service
    connection = create_connection()
    
    page_size = 100 # The largest possible page size is 100

    # Get reviewable HITs from MTurk
    hits = connection.get_reviewable_hits(page_size=page_size)
    for hit in hits:
        # A HIT can have multiple assignments
        assignments = connection.get_assignments(hit.HITId)
        for assignment in assignments:
            # Loop through the assignment collection to get the results 
            # of each question (as multiple questions can be attached
            # to a single assignment).
            for answer in assignment.answers[0]:
                for identifier, optionid in answer.fields:
                    # Record the answer in the database
                    campaignid, termid = identifier.split("|")
                    answer = CampaignAnswer(hit.HITId, 
                                            assignment.WorkerId,
                                            campaignid,
                                            termid,
                                            optionid)
                    db.session.add(answer)
                    results_returned = True
    # Save answers to the database
    db.session.commit()

    # Process the HIT approvals to prevent multiple attempts to save
    if len(hits) > 0:
        for hit in hits:
            assignments = connection.get_assignments(hit.HITId)
            for assignment in assignments:
                # Right now this is approving everything; that's probably
                # not going to be the correct behavior in the long term.
                connection.approve_assignment(assignment.AssignmentId)
            # Now that the assignments have been handled, disable the HIT
            connection.disable_hit(hit.HITId)
    return results_returned
