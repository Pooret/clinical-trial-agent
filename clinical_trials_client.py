# clinical_trials_client.py

import requests
import json
import time

# --- Constants ---
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_PAGE_SIZE = 100 # Define a default page size

# --- Helper Function to Extract Data from a Single Study ---
def _extract_study_data(study_dict):
    """
    Extracts desired fields from a single study JSON object.

    Args:
        study_dict (dict): The dictionary representing a single study
                           from the API response.

    Returns:
        dict: A dictionary containing the extracted fields, or None if
              essential data is missing or an error occurs.
    """
    extracted_info = {}
    nct_id = 'Not Available' # Default value

    try:
        protocol = study_dict.get('protocolSection', {})

        # --- Identification ---
        id_module = protocol.get('identificationModule', {})
        nct_id = id_module.get('nctId', 'Not Available')
        title = id_module.get('briefTitle', 'Not Available')

        # --- Status ---
        status_module = protocol.get('statusModule', {})
        status = status_module.get('overallStatus', 'Not Available')
        start_date = status_module.get('startDateStruct', {}).get('date', 'Not Available')
        completion_date = status_module.get('completionDateStruct', {}).get('date', 'Not Available')

        # --- Design ---
        design_module = protocol.get('designModule', {})
        phases = design_module.get('phases', [])
        study_type = design_module.get('studyType', 'Not Available')
        enrollment = design_module.get('enrollmentInfo', {}).get('count', None)

        # --- Conditions ---
        cond_module = protocol.get('conditionsModule', {})
        conditions = cond_module.get('conditions', [])
        keywords = cond_module.get('keywords', [])

        # --- Eligibility ---
        elig_module = protocol.get('eligibilityModule', {})
        eligibility = elig_module.get('eligibilityCriteria', 'Not Available')

        # --- Interventions ---
        interv_module = protocol.get('armsInterventionsModule', {})
        interventions_list = interv_module.get('interventions', [])
        intervention_names = [interv.get('name', 'N/A') for interv in interventions_list]

        # --- Description ---
        desc_module = protocol.get('descriptionModule', {})
        brief_summary = desc_module.get('briefSummary', 'Not Available')

        # --- Outcomes ---
        outcome_module = protocol.get('outcomesModule', {})
        primary_outcomes_list = outcome_module.get('primaryOutcomes', [])
        primary_outcome_measures = [outcome.get('measure', 'N/A') for outcome in primary_outcomes_list]

        # --- Locations ---
        contact_loc_module = protocol.get('contactsLocationsModule', {})
        locations_list = contact_loc_module.get('locations', [])
        location_info = [f"{loc.get('city', 'N/A')}, {loc.get('country', 'N/A')}" for loc in locations_list]

        # --- Assemble Dictionary ---
        extracted_info = {
            'NCT ID': nct_id, 'Title': title, 'Status': status, 'Phases': phases,
            'Conditions': conditions, 'Keywords': keywords, 'Study Type': study_type,
            'Enrollment': enrollment, 'Interventions': intervention_names,
            'Brief Summary': brief_summary, 'Primary Outcome Measures': primary_outcome_measures,
            'Eligibility Criteria': eligibility, 'Start Date': start_date,
            'Completion Date': completion_date, 'Locations': location_info
        }
        return extracted_info

    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error extracting data for study {nct_id}: {e}")
        return None # Return None if extraction fails for a study


# --- Main Function to Fetch All Trials ---
def fetch_all_trials(query_params, max_pages=10, page_size=DEFAULT_PAGE_SIZE):
    """
    Fetches clinical trial data from the ClinicalTrials.gov API, handling pagination.

    Args:
        query_params (dict): Dictionary of query parameters (e.g., {'query.cond': 'diabetes'}).
                             'pageSize' and 'pageToken' will be added/updated by this function.
        max_pages (int): Maximum number of pages to fetch (safety limit). Default 10.
        page_size (int): Number of studies to request per page. Default 100.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              extracted information for one clinical trial. Returns an empty
              list if no studies are found or an error occurs.
    """
    all_extracted_studies = []
    current_page = 0
    local_query_params = query_params.copy() # Work on a copy
    local_query_params['pageSize'] = page_size

    print(f"Starting fetch with query: {query_params}")

    while True:
        current_page += 1
        if current_page > max_pages:
            print(f"Reached maximum page limit ({max_pages}). Stopping.")
            break

        print(f"Fetching page {current_page}...")

        try:
            response = requests.get(BASE_URL, params=local_query_params)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            print(f"Request failed on page {current_page}: {e}")
            break # Exit loop on request failure

        except json.JSONDecodeError as e:
             print(f"Failed to decode JSON on page {current_page}: {e}")
             print(f"Response text: {response.text[:500]}...") # Log part of the response
             break # Exit loop on JSON decode failure


        current_page_studies_raw = data.get('studies', [])
        if not current_page_studies_raw:
            print(f"No studies found on page {current_page}.")
            # break

        print(f"Extracting data from {len(current_page_studies_raw)} studies on page {current_page}...")
        for study_raw in current_page_studies_raw:
            extracted_data = _extract_study_data(study_raw)
            if extracted_data: # Only append if extraction was successful
                all_extracted_studies.append(extracted_data)

        # --- Check for the next page token ---
        next_page_token = data.get('nextPageToken')

        if next_page_token:
            print(f"Next Page Token found, preparing for next request...")
            local_query_params['pageToken'] = next_page_token
            # Remove query.cond/term? Sometimes needed, sometimes not. Test API behavior.
            # If removing helps: local_query_params.pop('query.cond', None)

            
            time.sleep(0.5)
        else:
            print("No next page token found. Finished fetching all pages.")
            break 

    print(f"\nFinished fetching. Total studies extracted: {len(all_extracted_studies)} across {current_page} page(s) attempted.")
    return all_extracted_studies


# --- Example Usage (when running the script directly) ---
if __name__ == "__main__":
    print("Running example fetch...")

    test_query = {'query.cond': 'diabetes'}

    # Call the main function, limit to 2 pages for testing
    results = fetch_all_trials(query_params=test_query, max_pages=2, page_size=20)

    if results:
        print(f"\nExample Results (first {min(3, len(results))} studies):")
        for i, study in enumerate(results[:3]):
            print(f"\n--- Study {i+1} ---")
            print(f"  NCT ID: {study.get('NCT ID')}")
            print(f"  Title: {study.get('Title')}")
            print(f"  Status: {study.get('Status')}")
            # Print other key fields if desired
    else:
        print("\nNo results returned from example fetch.")