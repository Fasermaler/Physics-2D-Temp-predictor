import os
os.environ['KIVY_GL_BACKEND'] = 'gl'
import kivy
import math
import numpy as np
import time as time2 # imports time as a different name to prevent conflict
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.graphics import Color
from w1thermsensor import W1ThermSensor
import csv
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

Builder.load_file("group9_temp2.kv")

sensor = W1ThermSensor()

class main_window(GridLayout):

    time = NumericProperty(0)


    def start(self, *_):

        self.get_temp = Clock.schedule_interval(self.Thermoprobe, 1)
        # Initializes the clock schedule for the timer
        self.count_up = Clock.schedule_interval(self.tick, 1)
        # Initializes the variables needed for regression and temp
        self.t_amb = sensor.get_temperature(W1ThermSensor.KELVIN) + 2
        self.tau = 15.97444089
        self.start_time = 0 # Starts the actual sensor clock
        self.data = []
        self.estimate = 273.15 # Initial estimate
        self.prev_estimate = 0
        self.t_current = None

        # Sets tha threshold value for temperature estimation termination
        self.threshold = 0.03

        # Flag that determines if estimation has terminated
        self.estimating = True

        # Counter flag for estimation logic
        self.counter = 0


    def tick(self, *_):
        if self.time >= 0:
            self.time += 1
        else:
            pass

    # Gets the temperature as well as predicts the temperature
    def Thermoprobe(self, *_):

        # Gets the temperature and displays it on the 'current temp' field
        self.t_current = sensor.get_temperature(W1ThermSensor.KELVIN)
        self.ids.ctemp.text = str(round((self.t_current - 273.15), 2))
        
        # While estimation is in progress:
        while self.estimating:

            # Loops until the ambient temperatures differ greatly
            while True:
                
                # Gets new temperature reading
                t_new = sensor.get_temperature(W1ThermSensor.KELVIN) + 2
                
                if (abs(self.t_amb - t_new) > 0.05):
                    
                    print("Beginning Estimation")

                    # Sets the prediction field to "starting estimation"
                    self.ids.ptemp.text = 'Starting Estimation'
                    
                    
                    self.start_time = time2.time()

                    # Changes estimation flag to False and breaks 
                    self.estimating = False
                    break
                # If there is no difference, t_new is the new ambient temperature
                else:

                    # Changes the text of the prediction field to "waiting"
                    self.ids.ptemp.text = 'Waiting...'

                    print("Current Temperature is {} K".format(t_new))
                    self.t_amb = t_new

        if (self.counter < 10) and (abs(self.prev_estimate - self.estimate) > self.threshold):

            # Linear regression code
            self.time_c = time2.time() - self.start_time      
            y = self.t_current - self.t_amb * math.e ** (-self.time_c / self.tau)
            x = 1 - math.e ** (-self.time_c / self.tau)
            self.data.append([x, y])
            
            xy = np.array(self.data)
            xx = xy[:, 0]
            yy = xy[:, 1]
            regr = linear_model.LinearRegression()
            regr.fit(xx.reshape(-1, 1), yy.reshape(-1, 1))
            
            # Sets the prevb estimate as the previous estimate
            self.prev_estimate = self.estimate
            # Sets the new estimate
            self.estimate = regr.coef_[0, 0] - 2.4  # PREDICTED TEMP
            

            # Updates predicted time and predicted temperature
            self.ids.ptime.text = str(int(self.time_c))
            self.ids.ptemp.text = "Predicting..."
            
            
            # prints the following in console for debug purposes
            print(time2.time() - self.start_time)
            print("Current Estimate of t_w is {} K, {} deg C".format(round(self.estimate, 3), round(self.estimate - 273.15, 3)))
        else:
            self.ids.ptemp.text = str(round((self.estimate - 273.15), 2))

        self.counter += 1



    def stop(self, *_):
        Clock.unschedule(self.count_up)
        Clock.unschedule(self.get_temp)

    def close(self, *_):
        App.get_running_app().stop()
        Window.close()

class main_windowApp(App):
    def build(self):
        return main_window(time=0)

if __name__== "__main__":
    display = main_windowApp()
    display.run()