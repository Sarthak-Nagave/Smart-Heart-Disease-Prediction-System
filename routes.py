from flask import render_template, request, redirect, url_for, flash, session
from app import app
import logging
from ml_models import HeartDiseasePredictor
from medical_data import get_disease_info, get_health_tips, get_diet_recommendations

# Initialize the ML predictor
predictor = HeartDiseasePredictor()

@app.route('/')
def landing():
    """Landing page with welcome message and start diagnosis button"""
    return render_template('landing.html')

@app.route('/input')
def input_form():
    """Input form page with health parameters"""
    return render_template('input_form.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        form_data = {}
        fields = [
            'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 
            'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'bmi',
            'smoking', 'alcohol_intake', 'physical_activity', 'stress_level',
            'family_history', 'diabetes', 'heart_rate_variability', 'valve_noise',
            'aortic_size', 'infection_history', 'congenital_defect'
        ]

        at_least_one_input = False

        for field in fields:
            value = request.form.get(field)
            if value and value.strip():
                at_least_one_input = True
                try:
                    form_data[field] = int(value) if field in [
                        'sex', 'cp', 'fbs', 'restecg', 'exang', 'slope', 'ca', 'thal',
                        'smoking', 'alcohol_intake', 'family_history', 'diabetes',
                        'valve_noise', 'infection_history', 'congenital_defect'
                    ] else float(value)
                except ValueError:
                    flash(f"Invalid value for {field}: {value}", 'error')

        if not form_data or len(form_data) < 3:  # Require at least 3 fields
            flash('Please fill in at least 3 health parameters for accurate prediction.', 'error')
            return redirect(url_for('input_form'))

        predictions = predictor.predict(form_data)

        session['form_data'] = form_data
        session['predictions'] = predictions
        return redirect(url_for('results'))

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        flash("An unexpected error occurred during prediction.", "error")
        return redirect(url_for('input_form'))

        # Make predictions
        predictions = predictor.predict(form_data)
        
        # Store in session for results page
        session['form_data'] = form_data
        session['predictions'] = predictions
        
        return redirect(url_for('results'))
        
    except Exception as e:
        logging.error(f"Error in prediction: {str(e)}")
        flash('An error occurred while processing your data. Please try again.', 'error')
        return redirect(url_for('input_form'))

@app.route('/results')
def results():
    """Results page with predictions and recommendations"""
    try:
        predictions = session.get('predictions')
        form_data = session.get('form_data')
        
        if not predictions or not form_data:
            flash('No prediction data found. Please complete the form first.', 'error')
            return redirect(url_for('input_form'))
        
        # Get detailed information for each predicted condition
        detailed_results = []
        for condition, data in predictions.items():
            if data['risk_level'] != 'Low':  # Only show significant risks
                disease_info = get_disease_info(condition)
                health_tips = get_health_tips(condition, form_data)
                diet_recommendations = get_diet_recommendations(condition, form_data)
                
                detailed_results.append({
                    'condition': condition,
                    'probability': data['probability'],
                    'risk_level': data['risk_level'],
                    'confidence': data['confidence'],
                    'disease_info': disease_info,
                    'health_tips': health_tips,
                    'diet_recommendations': diet_recommendations
                })
        
        return render_template('results.html', 
                             results=detailed_results, 
                             form_data=form_data)
        
    except Exception as e:
        logging.error(f"Error in results: {str(e)}")
        flash('An error occurred while displaying results. Please try again.', 'error')
        return redirect(url_for('input_form'))

@app.route('/reset')
def reset():
    """Clear session and return to landing page"""
    session.clear()
    return redirect(url_for('landing'))
