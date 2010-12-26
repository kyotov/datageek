import os
import pprint
import time

import tcx

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
    def get(self):
        values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, values))

class TCX_fetch(webapp.RequestHandler):
    def get(self):
        values = {}
        path = os.path.join(os.path.dirname(__file__), 'TCX_fetch.html')
        self.response.out.write(template.render(path, values))
 
class TCX_fetch_process(webapp.RequestHandler):
    def check(self, condition, message = 'error'):
        if not condition:
            raise Exception(message)
    def getFloat(self, value):
        if value is None:
            return(None)
        else:
            return(float(value))
    def getPosition(self, position):
        if position is None:
            return(None)
        else:
            return((
                    self.getFloat(position.LatitudeDegrees),
                    self.getFloat(position.LongitudeDegrees)
                    ))
    def getBpm(self, bpm):
        if bpm is None:
            return(None)
        else:
            return(int(bpm.Value))
    def getRunCadence(self, tp):
        if tp.Extensions is None or tp.Extensions.TPX is None:
            return(None)
        else:
            return(int(max([tpx.RunCadence for tpx in tp.Extensions.TPX])))
    def getSpeed(self, tp):
        if tp.Extensions is None or tp.Extensions.TPX is None:
            return(None)
        else:
            return(float(max([tpx.Speed for tpx in tp.Extensions.TPX])))
    def translate(self, tcx):
        self.check(tcx is not None)
        self.check(tcx.Activities is not None)
        self.check(tcx.Activities.Activity is not None)
        self.check(len(tcx.Activities.Activity) == 1)
        v = tcx.Author.Build.Version
        a = tcx.Activities.Activity[0] 
        result = {'author': tcx.Author.Name,
                  'author.part_number': tcx.Author.PartNumber,
                  'author.lang_id': tcx.Author.LangID,
                  'author.version': {'build_major': int(v.BuildMajor),
                                     'build_minor': int(v.BuildMinor),
                                     'version_major': int(v.VersionMajor),
                                     'version_minor': int(v.VersionMinor)
                                     },
                  'creator': a.Creator.Name,
                  'creator.product_id': int(a.Creator.ProductID),
                  'creator.unit_id': int(a.Creator.UnitId),
                  'creator.version': {'build_major': int(a.Creator.Version.BuildMajor),
                                      'build_minor': int(a.Creator.Version.BuildMinor),
                                      'version_major': int(a.Creator.Version.VersionMajor),
                                      'version_minor': int(a.Creator.Version.VersionMinor)
                                      },
                  'laps': [{'avg_bpm': self.getBpm(lap.AverageHeartRateBpm),
                            'max_bpm': self.getBpm(lap.MaximumHeartRateBpm),
                            'avg_spm': int(max([lx.AvgRunCadence for lx in lap.Extensions.LX])),
                            'max_spm': int(max([lx.MaxRunCadence for lx in lap.Extensions.LX])),
                            'avg_speed': float(max([lx.AvgSpeed for lx in lap.Extensions.LX])),
                            'max_speed': float(lap.MaximumSpeed),
                            'distance_meters': float(lap.DistanceMeters),
                            'start_time': time.strptime(lap.StartTime, '%Y-%m-%dT%H:%M:%S.000Z'),
                            'total_time_seconds': float(lap.TotalTimeSeconds),
                            'calories': int(lap.Calories),
                            'trigger_method': lap.TriggerMethod,
                            'points': [{
                                        'altitude_meters': self.getFloat(tp.AltitudeMeters),
                                        'distance_meters': self.getFloat(tp.DistanceMeters),
                                        'position': self.getPosition(tp.Position),
                                        'time': time.strptime(tp.Time, '%Y-%m-%dT%H:%M:%S.000Z'),
                                        'bpm': self.getBpm(tp.HeartRateBpm),
                                        'spm': self.getRunCadence(tp),
                                        #'speed': self.getSpeed(tp)
                                        } for tp in lap.Track[0].Trackpoint]
                            } for lap in a.Lap]
                  }
        return result
    def post(self):
        values = { 'error' : 'ok', 'result' : 'ok1' }
        try:
            result = urlfetch.Fetch(url=self.request.get('tcx_url'))
            if result.status_code == 200:
                doc = tcx.parseString(result.content)
                doc2 = self.translate(doc)
                values = { 'result' : '<pre>' + pprint.pformat(doc2, indent = 4, depth = 10, width = 10) + '</pre>' }
            else:
                #self.response.out.write('crap!')
                values = { 'result' : 'crap!' }
        except Exception, e: 
            values = { 'result' : str(e) }            
        path = os.path.join(os.path.dirname(__file__), 'TCX_fetch_process.html')
        self.response.out.write(template.render(path, values))
                           
# http://connect.garmin.com/proxy/activity-service-1.0/tcx/activity/59598980?full=true

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      
                                      ('/TCX_fetch', TCX_fetch),
                                      ('/TCX_fetch_process', TCX_fetch_process)
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()