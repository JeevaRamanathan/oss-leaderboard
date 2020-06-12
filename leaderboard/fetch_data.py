""" Fetch required data from the GitHub API. """
import os
import json
import logging
from typing import Dict

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from leaderboard.utils.formatter import convert_to_intermediate_table
from leaderboard.utils.intermediate_score_table import get_intermediate_score_table
from leaderboard.utils.final_score_table import get_final_score_table
from leaderboard.utils.data import convert_df_to_markdown

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("fetch_data")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
API_ENDPOINT = "https://api.github.com/graphql"

headers = {"Authorization": GITHUB_TOKEN}

logger.info(headers)


def execute_query(query: str, variables: Dict):
    """ Executes query to fetch data from GraphQL API.

	Args:
		query: GraphQL query for fetching data.
		username: whose data will be fetched.
	"""
    s = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=(["POST"]),
    )

    s.mount("https://", HTTPAdapter(max_retries=retries))

    request = s.post(
        url=API_ENDPOINT,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=20,
    )

    if request.status_code == 200:
        logger.info(json.dumps(request.json(), indent=4))

        intermediate_table = convert_to_intermediate_table(
            json.dumps(request.json(), indent=4)
        )
        
        intermediate_score_table = get_intermediate_score_table(intermediate_table)
        final_score_table = get_final_score_table(intermediate_score_table)
        convert_df_to_markdown(final_score_table)


        with open("data.json", "w") as f:
            json.dump(request.json(), f, indent=4)
    else:
        raise Exception(
            "Request failed with code of {} \n{}.".format(
                request.status_code, request.text
            )
        )
