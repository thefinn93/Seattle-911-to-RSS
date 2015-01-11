#!/usr/bin/env python
import logging
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, request
from werkzeug.contrib.atom import AtomFeed


def checkForIncidents():
    url = "https://www2.ci.seattle.wa.us/fire/realtime911/"
    url += "getRecsForDatePub.asp?action=Today&incDate=&rad1=des"
    raw = requests.get(url, verify=False).content
    soup = BeautifulSoup(raw)
    rows = soup.find_all("table")[3].find_all("tr")
    incidents = []
    for row in rows:
        try:
            tds = row.find_all("td")
            a = {}
            a['active'] = "active" in tds[1].get("class")
            if len(tds[0].contents) > 0:
                a['date'] = datetime.strptime(tds[0].contents[0],
                                              "%m/%d/%Y %I:%M:%S %p")
            else:
                a['date'] = "Unknown"
                logging.warning("Date missing!")
            if len(tds[1].contents) > 0:
                a['number'] = tds[1].contents[0]
            else:
                a['number'] = "Unknown"
                logging.warning("Incident number missing!")
            if len(tds[2].contents) > 0:
                a['level'] = tds[2].contents[0]
            else:
                a['level'] = "Unknown"
                logging.warning("Level missing for incident %s", a['number'])
            if len(tds[3].contents) > 0:
                a['units'] = tds[3].contents[0]
            else:
                a['units'] = "Unknown"
                logging.warning("Units missing for incident %s", a['number'])
            if len(tds[4].contents) > 0:
                a['location'] = tds[4].contents[0]
            else:
                a['location'] = "Unknown"
                logging.warning("Location missing for incident %s",
                                a['number'])
            if len(tds[5].contents) > 0:
                a['type'] = tds[5].contents[0]
            else:
                a['type'] = "Unknown"
                logging.warning("Type missing for incident %s", a['number'])
            incidents.append(a)
        except IndexError:
            logging.info(row.prettify())
    return incidents

app = Flask(__name__)


@app.route("/911.atom")
def atom911():
    feed = AtomFeed('911 Calls',
                    feed_url=request.url,
                    url=request.url_root)
    for incident in checkForIncidents():
        title = "%s #%s" % (incident['type'], incident['number'])
        body = "<table>\n"
        for key in incident:
            body += "<tr><td><b>%s</b></td><td>%s</td></tr>\n" % (key, incident[key])
        body += "</table>"
        feed.add(title, body, content_type='html', published=incident['date'],
                 id=incident['number'], updated=incident['date'])
    return feed.get_response()


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial


@app.route("/911.json")
def json911():
    return json.dumps(checkForIncidents(), default=json_serial)


if __name__ == "__main__":
    app.run(debug=True)
