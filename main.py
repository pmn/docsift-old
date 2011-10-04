from flask import Flask, render_template, request, redirect, url_for, flash, Response
from forms import NewCampaignForm

from models import db, Campaign, CampaignOption, CampaignTerm, CampaignAnswer
from mturk import create_campaign_hits, retrieve_reviewable_hits

import json
import sys
import re

import settings

app = Flask(__name__)

db.create_all()

### Application Routes ###
@app.route('/')
def home():
    """
    Redirect all requests to the campaign list for now.
    """
    return redirect(url_for('listcampaigns'))

@app.route('/campaigns')
def listcampaigns():
    """
    List all the campaigns. 
    """
    campaigns = Campaign.query.all()
    
    # Report whether or not there are jobs pending
    pending_jobs = False
    for campaign in campaigns:
        if (campaign.job_generated == True) and (len(campaign.answers) == 0):
            pending_jobs = True

    return render_template('campaignlist.html', campaigns=campaigns, pending_jobs=pending_jobs)

@app.route('/campaigns/new', methods=['GET','POST'])
def newcampaign():
    """
    Create a new campaign. 

    MTurk jobs are spawned after the campaign is created.
    """
    form = NewCampaignForm(request.form)
    if request.method == 'POST' and form.validate():
        # Add the campaign itself
        campaign = Campaign(form.title.data, 
                            form.question.data, 
                            form.terms_per_quiz.data, 
                            form.reward.data, 
                            form.times_per_term.data)
        db.session.add(campaign)

        # Add the options 
        options = re.split(r'[\n\r]+', form.options.data)
        for option in options:
            if len(option) > 0:
                campaign_option = CampaignOption(campaign, option)
                db.session.add(campaign_option)

        # Add the terms
        terms = re.split(r'[\n\r]+', form.terms.data)
        for term in terms:
            if len(term) > 0:
                campaign_term = CampaignTerm(campaign, term)
                db.session.add(campaign_term)

        # Save everything to the db
        db.session.commit()
        return redirect(url_for('campaigndetails',id=campaign.id))
    return render_template('newcampaign.html',form=form)

@app.route('/campaigns/<id>')
def campaigndetails(id):
    """  
    Because campaign creation spawns a bunch of mturk jobs, campaigns are not editable. 
    If a campaign needs to be modified the old (incorrect) campaign should be deleted
    and a new campaign added in its place. 
    """
    campaign = Campaign.query.filter_by(id=id).first_or_404()

    # Figure out what the first option ID is so the responses can be color-coded    
    firstoptionid = 10000
    for option in campaign.options:
        if option.id < firstoptionid:
            firstoptionid = option.id

    return render_template('campaigndetails.html', 
                           campaign=campaign, 
                           firstoptionid=firstoptionid,
                           resultset=campaign.get_results())

@app.route('/campaigns/<id>.<filetype>')
def downloadresults(id, filetype):
    """
    Emit a parseable version of the campaign results for external consumption.
    """
    campaign = Campaign.query.filter_by(id=id).first_or_404()
    results = campaign.get_result_dump()

    if filetype == "csv":
        # Build the CSV header
        out = "\"term\", \"answer\""
        
        # Include each possible option in the header
        for option in campaign.options:
            out += ", \"%s\"" % option.option_text 
        
        # Create a newline before attaching the results
        out += "\r\n"
        
        # Add the results to the CSV
        for i in range(len(results)):
            out += "\"%s\", \"%s\"" % (results[i][0], results[i][1])
            
            # Loop through the answer breakdown to provide supporting data
            for option in campaign.options:
                out += ", \"%s\"" % results[i][2][option.option_text]

            # Add a new line before going to the next result
            out += "\r\n"
            
        return Response(out, mimetype='text/csv')
    elif filetype == "json":
        # Returning JSON is as simple as it gets:
        return Response(json.dumps(results,indent=2), mimetype='text/json')
    else:
        return "Unknown filetype."
     

@app.route('/campaigns/<id>/delete', methods=['GET','POST'])
def deletecampaign(id):
    """
    Delete an existing campaign. 

    Because campaigns are tied to MTurk jobs, jobs will need to be cancelled where
    possible when the campaign is deleted (otherwise there will be jobs running 
    and the results will never be collected, wasting money).
    """
    campaign = Campaign.query.filter_by(id=id).first_or_404()
    if request.method == 'POST':
        campaignname = campaign.title
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign "%s" was deleted!' % campaignname)
        return redirect(url_for('listcampaigns'))
    return render_template('deletecampaign.html', campaign=campaign)

@app.route('/campaigns/<id>/generate', methods=['POST'])
def generatecampaign(id):
    """
    Generate MTurk jobs for the campaign represented by 'id'
    """
    create_campaign_hits(id)
    flash("Mechanical Turk campaign created!")
    return redirect(url_for('listcampaigns'))

@app.route('/fetchresults', methods=['POST'])
def fetchresults():
    if retrieve_reviewable_hits() == False:
        flash("There were no results, wait a few minutes and try again")
    return redirect(url_for('listcampaigns'))

### Application settings ###
app.secret_key = settings.APP_SECRET_KEY

if __name__ == '__main__':
    app.run(debug=True)
