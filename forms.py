from flaskext.wtf import Form, DecimalField, IntegerField, TextField, TextAreaField, NumberRange,  Required

class NewCampaignForm(Form):
    title = TextField('Campaign Name', validators=[Required()])
    question = TextField('Question to ask (i.e. Would a vegetarian eat [term]?) \
                          <span class="tip">[term] is substituted with terms specified below</span>', 
                         validators=[Required()])
    options = TextAreaField('Answers, separated by newlines',
                            validators=[Required()])
    terms = TextAreaField('Terms to test, separated by newlines', 
                          validators=[Required()])
    terms_per_quiz = IntegerField('How many terms should be presented on each quiz?', 
                                validators=[NumberRange(min=0, max=50, 
                                            message='Specify fewer than 50 terms per quiz')])
    reward = DecimalField('How much to reward per quiz?', 
                          validators=[NumberRange(min=0.01, max=5.00, 
                                      message='Reward should be between .01 and 5.00')])
    times_per_term = IntegerField('How many times should each quiz be presented?',
                                    validators=[NumberRange(min=1,max=50)]) 
  
