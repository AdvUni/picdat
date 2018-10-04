"""
Is responsible to write a html file containing the required charts.
"""
import logging

from general import constants

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2018, Advanced UniByte GmbH'

# license notice:
#
# This file is part of PicDat.
# PicDat is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public (at your option) any later version.
#
# PicDat is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with PicDat. If not,
# see <http://www.gnu.org/licenses/>.


def create_chart_buttons(html_document, chart_id):
    """
    Creates two html buttons - 'select all' and 'deselect all' - which allow selecting or
    deselecting all checkboxes and with this all graph lines of one chart at once.
    Additionally, creates a toggle button called 'stacked', which toggles the dygraphs option
    'stacked'. Further, creates a text field which is for filtering the visible graph lines and a
    second toggle button which can reverse the filter.
    :param html_document: The html file, the chart buttons should be written in.
    :param chart_id: The id of the chart, the buttons should belong to.
    :return: None
    """
    html_document.write('<div class="chartbuttondiv">\n')
    # select button
    html_document.write('    <button type="button" class="selectbtn" onclick="selectAll(this, %s'
                        ')">select all</button>\n' % chart_id)
    # deselect button
    html_document.write('    <button type="button" class="selectbtn" onclick="deselectAll(this, '
                        '%s)">deselect all</button>\n' % chart_id)
    # stacked toggle button / checkbox
    html_document.write('    <div class="checkdiv"><label><input type="checkbox" '
                        'onclick="toggleStacked(this.checked, %s)">'
                        '<span>stacked</span></label></div>\n' % chart_id)

    reverse_filter_id = chart_id + '_filter'
    # filter text field
    html_document.write('    <input type="text" onkeypress="filter(event.keyCode, %s, this.value, '
                        'document.getElementById(\'%s\').checked)">\n'
                        % (chart_id, reverse_filter_id))
    # reverse filter toggle button / checkbox
    html_document.write('    <div class="checkdiv"><label><input type="checkbox" id="%s">'
                        '<span>reverse filter</span></label></div>\n' % reverse_filter_id)
    html_document.write('</div>\n')


def write_template(html_document, compact):
    """
    Copies the content of the html template into the html document. Decides between two templates,
    depending on the compact boolean.
    :param html_document: File object, where to write the template to.
    :param compact: Boolean, which says whether command line option 'compact' is set or not. If so,
    uses the HTML_TEMPLATE_COMPACT, which already includes all the dygraphs code.
    :return: None.
    """
    if compact:
        html_template = constants.HTML_TEMPLATE_COMPACT
    else:
        html_template = constants.HTML_TEMPLATE
    with open(html_template, 'r') as template:
        html_document.writelines(template.readlines())


def create_tab_button(html_document, tab_name, tab_charts):
    """
    Writes an html button element of class 'tablinks' into html_document. Buttons of this class
    will be arranged in a tab bar.
    :param html_document: File object, where to write the button to.
    :param tab_name: button text, describing the kind of charts belonging to this tab.
    :param tab_charts: chart id's of the charts belonging to this tab.
    :return: None.
    """
    tab_charts_str = str(tab_charts[0])
    for chart in tab_charts[1:]:
        tab_charts_str += ', '
        tab_charts_str += str(chart)

    html_document.write('    <button class="tablinks" onclick="openTab(event, '
                        +"'" + tab_name + "', [" + tab_charts_str + '])">' + tab_name
                        +'</button>\n')


def create_html(html_filepath, csv, html_title, label_dict, compact_file):
    """
    Writes an html file which visualizes the contents of csv tables in a nice way.
    :param html_filepath: The path the html file should be saved at.
    :param csv: Either a list of strings referencing csv files, or a list of the raw csv data
    itself.
    :param html_title: Some string describing the processed performance data, for example naming
    the cluster and the node. Will be written to the top of the html document.
    :param label_dict: A dict containing meta data such as axis labels or names for the charts
    the tables)
    :param compact: Boolean, which says whether command line option 'compact' is set or not. If so,
    dygraphs code and csv content will be included into the html.
    :return: None
    """

    titles = [first_str + ': ' + second_str for first_str, second_str in label_dict['identifiers']]
    chart_ids = [first_str.replace(':', '_').replace(
        '-', '_') + '_' + second_str for first_str, second_str in label_dict['identifiers']]
    y_labels = label_dict['units']
    x_labels = ['bucket' if is_histo else 'time' for is_histo in label_dict['is_histo']]
    barchart_booleans = ['true' if is_histo else 'false' for is_histo in label_dict['is_histo']]

    tabs = []
    tabs_dict = {}
    for i in range(len(label_dict['identifiers'])):
        first_str, _ = label_dict['identifiers'][i]
        if first_str not in tabs:
            tabs.append(first_str)
            tabs_dict[first_str] = []
        tabs_dict[first_str].append(i)

    with open(html_filepath, 'w') as html_document:
        # write template, including js code
        write_template(html_document, compact_file)

        # write caption
        html_document.write('    <h1> ' + html_title + ' </h1>\n')
        # write timezone notice
        if 'timezone' in label_dict:
            html_document.write('    <h2> ' + 'timezone: '
                                +label_dict['timezone'] + ' </h2>\n')

        # write tab buttons:
        html_document.write('<div class="tab">\n')
        for tab in tabs:
            tab_charts = [chart_ids[i] for i in tabs_dict[tab]]
            create_tab_button(html_document, tab, tab_charts)
        html_document.write('</div>\n')

        # write rest of body
        for tab in tabs:
            html_document.write('<div id="' + tab + '" class="tabcontent">\n')
            for chart_nr in tabs_dict[tab]:
                # call js function to create Dygraph objects
                html_document.write('<script> ' + chart_ids[chart_nr] + ' = makeChart("'
                                    +chart_ids[chart_nr] + '", "' + tab + '", '
                                    +repr(csv[chart_nr]) + ', "'
                                    +titles[chart_nr]
                                    +'", "' + x_labels[chart_nr] + '", "'
                                    +y_labels[chart_nr] + '", ' + barchart_booleans[chart_nr]
                                    +'); </script>')

                # create 'select all' and 'deselect all' buttons
                create_chart_buttons(html_document, chart_ids[chart_nr])
            html_document.write('</div>\n')

        # end html document
        html_document.write('</body>\n</html>')

    logging.info('Generated html file at %s', html_filepath)
