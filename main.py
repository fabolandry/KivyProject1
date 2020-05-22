import boto3
import json
import kivy
from urllib.request import urlopen
from boto3.dynamodb.conditions import Key
from kivymd.app import MDApp

kivy.require("1.11.1")
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivymd.uix.picker import MDDatePicker


class WelcomeScreen(Screen):  # Defines WelcomeScreen instance as a screen widget.
    pass


class DateScreen(Screen):  # Defines DateScreen instance as a screen widget.
    pass


class ResultScreen(Screen):  # Defines ResultScreen instance as a screen widget.
    pass


kv = """
ScreenManager:
    WelcomeScreen:
        name: 'my_welcome_screen'
        id: my_welcome_screen
    DateScreen:
        name: 'my_date_screen'
        id: my_date_screen
    ResultScreen:
        name: 'myresultscreen'
        id: myresultscreen
<WelcomeScreen>:
    _welcome_screen_text_: welcome_screen
    name: 'my_welcome_screen'
    id: my_welcome_screen
    Label:
        id: welcome_screen
        Image: 
            source: 'Cheers.jpg'
            size: 200, 200
            center: self.parent.center

<DateScreen>:
    name: 'my_date_screen'
    id: my_date_screen
    BoxLayout:
        padding: dp(10)
        size_hint: None, None
        size: self.minimum_size
        spacing: dp(10)
        orientation: "vertical"
        pos_hint: {'center_x': .5, 'center_y': .5}
        MDRaisedButton:
            text: 'Select a Date'
            theme_text_color: 'Custom'
            text_color: [1, 1, 1, 1]
            md_bg_color: [0, 0, 0, 1]
            on_release:
                app.show_datepicker()

<ResultScreen>:
    name: 'myresultscreen'
    id: myresultscreen
    RecycleView:
        id: rv
        scroll_type: ['bars', 'content']
        viewclass: 'Label'
        RecycleBoxLayout:
            default_size: None, dp(56)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'             
"""


class MainApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.root_widget = Builder.load_string(kv)
        Clock.schedule_once(self.screen_switch_two, 3)  # clock callback for the DateScreen
        return self.root_widget

    def screen_switch_two(self, dt):
        self.root_widget.current = 'my_date_screen'  # switches screen using Screen Managers current method and desired screens name.

    def show_datepicker(self):
        picker = MDDatePicker(callback=self.got_date)
        picker.open()

    def got_date(self, thedate):
        the_date = str(thedate)
        if check_db(the_date) == []:
            collect_data(the_date)
        returned_list = check_db(the_date)
        print('List Lenght: ' + str(len(returned_list)))
        formated_list = []
        for i in range(0, len(returned_list)):
            formated_str1 = '---------- NEO ' + str(i + 1) + '  Date: ' + the_date + ' ---------- '
            formated_list.append(formated_str1)
            formated_str2 = 'Object Name: ' + str(returned_list[i]['Name'])
            formated_list.append(formated_str2)
            formated_str3 = 'Exact Time: ' + str(returned_list[i]['Complete_Date'])
            formated_list.append(formated_str3)
            formated_str4 = 'Hazardousness: ' + str(returned_list[i]['Dangerosity'])
            formated_list.append(formated_str4)
            formated_str5 = 'miss distance (miles): ' + str(returned_list[i]['Miss_distance'])
            formated_list.append(formated_str5)
            formated_str6 = 'Object Diameter (miles): ' + str(returned_list[i]['Diameter'])
            formated_list.append(formated_str6)
            formated_str7 = 'Object Speed (miles/hr): ' + str(returned_list[i]['Speed'])
            formated_list.append(formated_str7)
        print(formated_list)
        self.root_widget.current = 'myresultscreen'
        self.root_widget.ids.myresultscreen.ids.rv.data = [{'text': k} for k in formated_list]
        return formated_list


# -------------------Checking if the value is in the DB table-------------------------------

def check_db(value):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('NEOTABLE')
    response = table.query(KeyConditionExpression=Key('Date').eq(value))
    return response['Items']


# -------------------Collecting data and storing them into DB-------------------------------

def collect_data(input_value):
    url = 'https://api.nasa.gov/neo/rest/v1/feed?start_date={}&end_date={}&api_key=PGHOjkaiXMjUw5Wz7r35gIwdUN9DrhUaJ5EoIGPM'.format(
        input_value, input_value)
    jsonurl = urlopen(url)
    text = json.loads(jsonurl.read())
    total_num = text['element_count']
    lst = []
    i = 0
    while i < total_num:
        for item in text['near_earth_objects'][input_value]:
            dic = {}
            dic['Date'] = input_value
            dic['Name'] = text['near_earth_objects'][input_value][i]['name']
            dic['Dangerosity'] = text['near_earth_objects'][input_value][i]['is_potentially_hazardous_asteroid']
            dic['Complete_Date'] = text['near_earth_objects'][input_value][i]['close_approach_data'][0][
                'close_approach_date_full']
            dic['Speed'] = text['near_earth_objects'][input_value][i]['close_approach_data'][0]['relative_velocity'][
                'miles_per_hour']
            dic['Miss_distance'] = \
            text['near_earth_objects'][input_value][i]['close_approach_data'][0]['miss_distance']['miles']
            dic['Diameter'] = str(
                text['near_earth_objects'][input_value][i]['estimated_diameter']['miles']['estimated_diameter_max'])
            lst.append(dic)
            i = i + 1
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('NEOTABLE')
    for i in range(0, len(lst)):
        table.put_item(Item=lst[i])
    print('Data collected from NASA API and saved in Dynamodb')


if __name__ == '__main__':
    app = MainApp()
    app.run()