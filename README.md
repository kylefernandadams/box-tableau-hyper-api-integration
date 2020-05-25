# Box Tableau Hyper API Integration
This project pulls enterprise events from Box and inserts them into a Tableau Hyper file format using the [Hyper API](https://help.tableau.com/current/api/hyper_api/en-us/index.html).

## Pre-Requisites

1. Clone this github repo.
2. Create and authorize a JWT Application in the [Box Developer Console](https://account.box.com/developers/services) using the following [Setup Guide.](https://developer.box.com/en/guides/applications/custom-apps/jwt-setup/)
3. Install `hyper_box_events.py` dependencies:
    * [boxsdk](https://github.com/box/box-python-sdk#id1): Box Python SDK used to retrieve Box enterprise events.
    * [tableauhyperapi](https://help.tableau.com/current/api/hyper_api/en-us/reference/py/index.html): Used to insert Box events into a Hyper API file.
    * [tableauserverclient](https://tableau.github.io/server-client-python/docs/): Python client SDK for the Tableau REST APIs. This is used to publish the hyper file to a Tableau Server.
    * [dateutil](https://dateutil.readthedocs.io/en/stable/): Used for datetime conversion and parsing utilities.
4. Adjust the [limit](/hyper_box_events.py#L24) variable as needed.
    * More details on the [Enterprise Events Stream endpoint.](https://developer.box.com/reference/get-events/#request)
5. Run the [hyper_box_events.py](/hyper_box_events.py) Python script with the following parameters:
    * --box_config: Path to your JWT public/private configuration json file
    ```
    python3 hyper_box_events.py --box_config /path/to/my/box_config.json
    ```
6. Run the [publish_box_hyper.py](/publish_box_hyper.py) Python script with the following parameters:
    * --server: URL to your Tableau On-Prem or Online Server
    * --site_id: Name of your Tableau Site
    * --project_name: Name of the Project in which you want to upload the hyper file data source.
    * --hyper_file_path: Path to the box_events.hyper file created with the previous script.
    * --username: Username for you Tableau Server
    * --password: You can leave the value empty and the commandline will prompt you to enter a password.
    ```
    python3 publish_box_hyper.py --server https://me.online.tableau.com/ --site_id my_site --project_name Box --hyper_file_path /path/to/box_events.hyper --username me@example.com --password
    ```

## Tips and Tricks
You may want to combine the logic from the [hyper_box_events.py](/hyper_box_events.py) and [publish_box_hyper.py](/publish_box_hyper.py). I chose to decouple them in the event that you wanted to pull the hyper file directly into Tableau Desktop and not publish the data in an automated fashion.

## Disclaimer
This project is a collection of open source examples and should not be treated as an officially supported product. Use at your own risk. If you encounter any problems, please log an [issue](https://github.com/kylefernandadams/box-tableau-hyper-api-integration/issues).

## License

The MIT License (MIT)

Copyright (c) 2020 Kyle Adams

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
