import json
import sys
import requests

endpoint1_url = sys.argv[1]
endpoint2_url = sys.argv[2]

start_page = int(sys.argv[3])

def get_instance_meta(instance_url):
  return requests.get(instance_url).json()

instance1_meta = get_instance_meta(endpoint1_url)
instance2_meta = get_instance_meta(endpoint2_url)

people_api_url1 = instance1_meta['meta']['persons_api_url']
people_api_url2 = instance2_meta['meta']['persons_api_url']

def get_page(start_page, people_api_url):
  page = requests.get(people_api_url + '?page={}&embed=membership.organization'.format(start_page)).json()

  yield page

  while 'next_url' in page:
    page = requests.get(page['next_url'] + '&embed=membership.organization').json()

    yield page

def find_persons_name(person_name):
  url = endpoint2_url + u"search/persons?q=name:\"{}\"".format(person_name)

  resp = requests.get(url).json()

  for person in resp['result']:
    yield person

confirmed_matches = json.load(open('data/matches.json', 'r'))

def write_data(matches, path):
  json.dump(matches, open(path, 'w+'), indent=4, sort_keys=True)

for i, people_page in enumerate(get_page(start_page, people_api_url1)):
  print >>sys.stderr, "Page", start_page + i

  for person in people_page['result']:
    matches = list(find_persons_name(person['name']))

    for person_match in matches:
      if person['id'] in confirmed_matches and person_match['id'] in confirmed_matches[person['id']]:
        print "Skipping one match for {}".format(person['name'])
        continue

      standing_in = person_match.get('standing_in', {})
      if standing_in is None:
        standing_in = {}

      standing_in_2015 = standing_in.get('2015', None)

      if standing_in_2015 is not None:
        print "{} :: {}".format(person['name'], 'http://yournextmep.com/candidates/eu2014/' + person['identifiers'][0]['identifier'])

        print "  {} - {}, {}".format(person_match['name'], person_match['party_memberships']['2015']['name'], person_match['standing_in']['2015']['name']), 'http://yournextmp.com/person/{}'.format(person_match['id'])

        is_match = person['id'] in confirmed_matches and \
                   person_match['id'] in confirmed_matches[person['id']] and \
                   confirmed_matches[person['id']][person_match['id']]['match']

        if not is_match:
          input = raw_input('Real match Y/(N): ').upper()
          if input == 'Y':
            is_match = True
        else:
          input = raw_input('Real match (Y)/N: ').upper()
          if input == 'N':
            is_match = False

        match = {'yournextmep_url': person['url'],
                 'yournextmp_url': person_match['url'],
                 'name': person['name'],
                 'party_2015': person_match['party_memberships']['2015']['name'],
                 'constituency_2015': person_match['standing_in']['2015']['name'],
                 'match': is_match}

        if person['id'] not in confirmed_matches:
          confirmed_matches[person['id']] = {}

        confirmed_matches[person['id']][person_match['id']] = match

        write_data(confirmed_matches, 'data/matches.json')

