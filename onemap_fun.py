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


def onemap_xy_coordin(keyword: str) -> dict:
    """ 
    Extends onemap_location_best_match by allow for search results that originally only had one output
    """
    api_address = onemap_full_location_request(keyword)
    
    if api_address and len(api_address) == 1:
        result_xy = api_address[0]
        result_xy['search_keyword'] = keyword
        result_xy['score'] = np.nan
        
        for item in ['SEARCHVAL', 'BLK_NO', 'ROAD_NAME', 'BUILDING', 'ADDRESS', 'POSTAL', "LONGTITUDE"]:
            del result_xy[item]

    else:
        result_xy = onemap_location_best_match(keyword)
    
    return result_xy


def onemap_routing_url(start_end_lat_long: list,
                       route_type='drive') -> str:
    
    """ Provides start and end lat long and returns OneMap routing URL
        Default route_type is drive, but this can be changed to pt (public transport), cycle or walk
    """
    
    base_route_url = "https://developers.onemap.sg/privateapi/routingsvc/route?"
    long_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjEzODcsInVzZXJfaWQiOjEzODcsImVtYWlsIjoiY2xpZmZjaGV3ODRAZ21haWwuY29tIiwiZm9yZXZlciI6ZmFsc2UsImlzcyI6Imh0dHA6XC9cL29tMi5kZmUub25lbWFwLnNnXC9hcGlcL3YyXC91c2VyXC9zZXNzaW9uIiwiaWF0IjoxNjMzMDE5NzA2LCJleHAiOjE2MzM0NTE3MDYsIm5iZiI6MTYzMzAxOTcwNiwianRpIjoiMDA1MWYzOTM4ODBjNDdjNzkyN2Y2MDI0NjMwMzMyNDkifQ.U24KkqDbt8SUUdC_XBhM9NBj5u5MIc-p6OEie4dy3Cg"
    
    route_parameters = "start={},{}&end={},{}".format(start_end_lat_long[0], 
                                                      start_end_lat_long[1], 
                                                      start_end_lat_long[2], 
                                                      start_end_lat_long[3])
    
    url_route_type = "&routeType={}".format(route_type)
    
    return base_route_url + route_parameters + url_route_type + "&token=" + long_key

def get_onemap_total_dist_from_routing(start_end_lat_long: list):
    """ Provides start and end latlong and returns total distance of route
    """
    route_url = onemap_routing_url(start_end_lat_long)
    route = requests.get(route_url)
    return eval(route._content).get('route_summary').get("total_distance")

def get_onemap_routing_data(start_end_lat_long: list, parameter: str):
    """ Provides start and end latlong and returns total distance of route
    """
    route_url = onemap_routing_url(start_end_lat_long)
    route = requests.get(route_url)
    return eval(route._content).get('route_summary').get(parameter)
