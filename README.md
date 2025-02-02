# albert-heijn-calendar-sync
> Sync your Albert Heijn schedule with your Google calendar.

## How to use

- Change your settings in `src/settings.yaml`
    - Change the albert-heijn credentials.
    - Change the geckodriver path to your path.
    
- [Request](https://console.developers.google.com/flows/enableapi?apiid=calendar)
a google calendar api key and store the `client_secret.json` in `src/`. ([Guide on how to request a key](https://developers.google.com/google-apps/calendar/quickstart/python))
- Install the required dependencies.


## Dependencies

1. Google Client Library
2. Selenium
3. Beautifulsoup4
4. PyYAML
5. Requests
6. Httplib2
7. Six
8. Uritemplate
9. pyRFC3339
10. pytz
11. apiclient

#### Install requirements
    pip install -r requirements.txt

## View the browser

- Change the `showbrowser` setting in `src/settings.yaml` to true
- Change `geckopath` to your [geckodriver](https://github.com/mozilla/geckodriver/releases) path.
- Make sure you have [Firefox](https://www.mozilla.org/nl/firefox/new/) installed.
