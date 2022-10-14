import spacy
import json
import requests
import numpy as np
import en_core_web_sm
from typing import Optional

### Write some OneMap API functions
def onemap_location_request(search: str, page=1):
    """ 
    Extracts the first page result of the keyword location search from the OneMap API. The OneMap API can return more than 1 page of results, and this is dealt with another function. 
    """
    base = "https://developers.onemap.sg/commonapi/"
    api_query = base + 'search?searchVal={search}&returnGeom=Y&getAddrDetails=Y&pageNum={page}'.format(
        page=page, search=search
        )

    return requests.get(api_query)


def onemap_full_location_request(keyword: str) -> list:
    """ Returns all results based on keyword search on OneMap location as a list of dictionary key-value pairs with the following keys:
        'SEARCHVAL',
        'BLK_NO',
        'ROAD_NAME',
        'BUILDING',
        'ADDRESS',
        'POSTAL',
        'X',
        'Y',
        'LATITUDE',
        'LONGITUDE',
        'LONGTITUDE'
    """
    output = None
    api_request = onemap_location_request(keyword)

    # Get number of pagination from API call
    page_count = api_request.json().get('totalNumPages')
    
    try:
        if page_count > 0:
            api_results = []
            for i in range(1, page_count+1):
                api_results.append(
                    onemap_location_request(
                        keyword, page=i).json().get('results')
                    )

            output = [item for sublist in api_results for item in sublist]
    except:
        pass
    
    return output


def onemap_location_best_match(keyword: str) -> dict:
    """
    Returns OneMap API result that has the closest similarity match with the keyword searched
    """
    nlp = en_core_web_sm.load()
    high_value = 0
    index = 0

    result_list: Optional[list] = onemap_full_location_request(keyword)
    lowcase_keyword: str = nlp(keyword.lower())
    location_match: dict = {'search_keyword': keyword}

    if result_list:
        for i in range(len(result_list)):

            kw_2_check = nlp(result_list[i].get('SEARCHVAL').lower())
            kw_simi_score = lowcase_keyword.similarity(kw_2_check)
            if high_value < kw_simi_score:
                high_value = kw_simi_score
                index = i

        location_match = result_list[index]
        location_match['score'] = high_value
        location_match['search_keyword'] = keyword
        
        # Keeping only the necessary key-value pairs
        for item in ['SEARCHVAL', 'BLK_NO', 'ROAD_NAME', 'BUILDING', 'ADDRESS', 'POSTAL', "LONGTITUDE"]:
            del location_match[item]

    return location_match