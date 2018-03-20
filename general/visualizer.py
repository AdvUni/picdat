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


def graph_id(graph_title):
    """
    Generates a proper id for a graph to write in the html file.
    :param graph_title: The graph's title as string, you want to have an id for.
    :return: The id string.
    """
    return graph_title + '_graph'


def option_line(label, content, argument_is_string):
    """
    Generates a string to write it into an HTML file. It is used to specify an option inside the
    templates object.
    :param label: The option's label.
    :param content: The option's content.
    :param argument_is_string: Boolean, whether content should be written with quotation marks,
    because it is meant as String, or not, because it is meant as a javaScript function.
    :return: The line you can write into an HTML file.
    """
    if argument_is_string:
        return '            ' + label + ': "' + content + '",' + '\n'
    else:
        return '            ' + label + ': ' + content + ',' + '\n'


def get_legend_div_id(chart_id):
    """
    Generates a simple id for a chart legend's div element through adding a string to the chart id.
    :param chart_id: ID of the chart which legend should be carried by the div the ID is for.
    :return: simple ID as String
    """
    return chart_id + '_legend'


def create_select_buttons(html_document, chart_id):
    """
    Creates two html buttons - 'select all' and 'deselect all' - which allow selecting or
    deselecting all checkboxes and with this all graph lines of one chart at once.
    :param html_document: The html file, the checkboxes should be written in.
    :param chart_id: The id of the chart, the checkboxes should belong to.
    :return: None
    """
    html_document.write('<p>' + '\n')
    html_document.write('    <button type="button" onclick="selectAll(this, '
                        + chart_id + ', ' + "'" + chart_id + "'" +
                        ')">select all</button>' + '\n')
    html_document.write('    <button type="button" onclick="deselectAll(this, '
                        + chart_id + ', ' + "'" + chart_id + "'" +
                        ')">deselect all</button>' + '\n')
    html_document.write('</p>' + '\n')


def create_tab_button(html_document, tab_name, tab_charts):

    tab_charts_str = str(tab_charts[0])
    for chart in tab_charts[1:]:
        tab_charts_str += ', '
        tab_charts_str += str(chart)

    html_document.write('    <button class="tablinks" onclick="openTab(event, ' +
                        "'" + tab_name + "', [" + tab_charts_str + '])">' + tab_name +
                        '</button>\n')


def create_html(html_filepath, csv_files, html_title, label_dict):
    """
    Writes an html file which visualizes the contents of csv tables in a nice way.
    :param html_filepath: The path the html file should be saved at.
    :param csv_files: A list of file names from csv tables which should be visualized.
    :param html_title: A file path which is used as caption for the resulting html. Should be the
    path of the PerfStat output file.
    :param label_dict: A dict containing meta data such as axis labels or names for the charts
    the tables)
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
        # write head
        with open(constants.HTML_HEAD_TEMPLATE, 'r') as template:
            html_document.writelines(template.readlines())
        template.close()

        # write caption
        html_document.write('    <h2> ' + html_title + ' </h2>\n')
        # write timezone notice
        if 'timezone' in label_dict:
            html_document.write('    <h2> ' + 'timezone: ' +
                                label_dict['timezone'] + ' </h2>\n')

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
                html_document.write('<script> ' + chart_ids[chart_nr] + ' = makeChart("' +
                                    chart_ids[chart_nr] + '", "' + tab + '", "' + csv_files[chart_nr] + '", "' +
                                    titles[chart_nr] + '", "' + x_labels[chart_nr] + '", "' +
                                    y_labels[chart_nr] + '", ' + barchart_booleans[chart_nr] +
                                    '); </script>')

                # create 'select all' and 'deselect all' buttons
                create_select_buttons(html_document, chart_ids[chart_nr])
            html_document.write('</div>\n')

        # end html document
        html_document.write('</body>\n</html>')

    logging.info('Generated html file at %s', html_filepath)
