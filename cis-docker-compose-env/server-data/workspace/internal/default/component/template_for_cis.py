#!/usr/bin/python3
import requests

try:
    # When running in IDE
    import integration_services37 as cis
except:
    # When running in CIS (Docker)
    import integration_services as cis

import traceback

def main(task: cis.Task) -> None:
    try:

        data = task.get_data() # get the data from task

        if data is None or len(data) < 1:
            data = "No data sent in body/payload or task.set_data()"

        parms = get_all_parameters(task)
        givenname = parms['givenname']
        surname = parms['surname']

        text_name = f"Name: {givenname} {surname}"
        task.report_event(cis.re_normal, text_name) # Report to console in IDE
        task.report_event(cis.re_normal, f"Data: {data}") # Report to event_log in CIS.

        # Se all parameters on task
        task.report_event(cis.re_normal, task.get_parameters())

        # Fetch data from internet.
        # task.report_event(cis.re_normal, requests.get('http://www.aftonbladet.se').text)

        # Set data if integration was called/initiated from REST-client.
        task.set_data('200 OK')
        task.set_data('Content-Type: text/plain')
        task.set_data(f"Payload: {data} {text_name}")

    except Exception as exc:
        task.report_event(cis.re_warning, traceback.format_exc())
        task.report_event(cis.re_error, str(exc))
        task.quit()


def get_all_parameters(task: object) -> dict:
    parms = {
        'surname': task.get_parameter("surname"),
        'givenname': task.get_parameter("givenname"),
        'task': task,  # use in function with parms['task'].report_event(cis.re_normal, "Some text" )
    }

    # If sent by REST/Browser
    f_sur = task.get_parameter("FORM_SURNAME", "")
    f_giv = task.get_parameter("FORM_GIVENNAME", "")
    if len(f_sur) > 0:
        parms['surname'] = f_sur
    if len(f_giv) > 0:
        parms['givenname'] = f_giv

    return parms


if __name__ == '__main__':
    task = cis.new_task()

    task.set_data("Star Wars")
    task.set_parameter("givenname", "Obi-Wan")
    task.set_parameter("surname", "Kenobi")
    main(task)
    print(task.get_data())
    print(task.get_data())
    print(task.get_data())
