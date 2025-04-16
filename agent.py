import clinical_trials_client

# Get parameters from LLM parsing step (example)
api_params = {'query.cond': 'breast cancer'}

# Fetch the data
trial_data = clinical_trials_client.fetch_all_trials(query_params=api_params, max_pages=5)