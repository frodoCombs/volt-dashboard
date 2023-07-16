# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound

import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd


@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/check_form_name', methods=['POST'])
def check_form_name():
    # form_name = request.form.get('formName')
    # # Mock database of form names
    # existing_form_names = db.Model.query.with_entities(db.Model.column_name).all()
    # if form_name in existing_form_names:
    #     error_message = 'Form name already exists. Please choose a different name.'
    #     return jsonify(error=error_message)
    # else:
    #     return 'available'
    print("Pretending to check form name, success")
    return 'available'

def generate_plot_data(loans_dict, budget):
    print("\n\nIN GENERATE PLOT\n\n")
    total_paid = []
    total_debt = []
    debt = sum([loans_dict[k][0] for k in loans_dict.keys()])
    plot_data = {k:[] for k in loans_dict.keys()}
    # while there is still debt
    while debt > 0 :
        # calculate the amount of interest per loan over the next period
        interest = {}
        for k in loans_dict.keys():
            remaining_principal = min(loans_dict[k][0],loans_dict[k][2])
            interest[k] = (remaining_principal*loans_dict[k][1]/365)*30
        interest = {k: v for k, v in sorted(interest.items(), key=lambda item: item[1],reverse=True)}
        # update loan amounts with added interest
        for k in interest.keys():
            loans_dict[k][2] += int(interest[k])
        # determine which loan has the largest interest
        # pay off as much of that loan as possible given budget
        # if there is any left over, pay off the remainder of the budget to the next highest loan
        total_paid = []
        monthly_budget = budget
        for k in interest.keys():
            if monthly_budget == 0:
                break
            # make the payment
            if loans_dict[k][2] >= monthly_budget:
                total_paid.append(monthly_budget)
                loans_dict[k][2] -= monthly_budget
                monthly_budget -= monthly_budget
            elif loans_dict[k][2] < monthly_budget:
                monthly_budget -= loans_dict[k][2] 
                total_paid.append(loans_dict[k][2])
                loans_dict[k][2] = 0
        debt = sum([loans_dict[k][2] for k in loans_dict.keys()])
        total_debt.append(debt)
        for k in loans_dict.keys():
            plot_data[k].append(loans_dict[k][2])
    return plot_data, total_debt, total_paid

@blueprint.route('/submit', methods=['POST'])
def submit():
    print("\n\nIN SUBMIT PLOT\n\n")
    # Get form data
    form_name = request.form.get('formName') ### should be extended to contain user-name
    budget = float(request.form.get('budget')) ### should be extended to contain user-name
    principals = request.form.getlist('Principal')
    interests = request.form.getlist('Interest')
    loans_dict = {f"loan_{i}":[float(principals[i]),float(interests[i]),float(principals[i])] for i in range(len(principals))}
    plot_data, total_debt, total_paid = generate_plot_data(loans_dict, budget)
    # Generate the visualization
    fig = make_subplots(rows=1, cols=1)
    for k in plot_data.keys():
        fig.add_trace(go.Scatter(x=np.arange(len(plot_data[k])), y=plot_data[k], name = k))
    # print(f"Total paid over {len(total_paid)} 30-day months: {sum(total_paid)}")
    plot_html = fig.to_html(full_html=False)
    print(f"Created plot")
    return render_template('home/submit.html', plot_html=plot_html)


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
