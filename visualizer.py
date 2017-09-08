"""
Is responsible to write a html file containing the required charts.
"""
import constants
import util
import os

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2017, Advanced UniByte GmbH'


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


def style_line():
    """
    Generates a string to write it into an HTML file. It contains a line configuring the style.
    :return: The line you can write into an HTML file.
    """
    width_px = constants.CHARTS_WIDTH
    height_px = constants.CHARTS_HEIGHT
    return '     style="width: ' + str(width_px) + 'px; height: ' + str(height_px) + \
           'px;"></div>' + os.linesep


def option_line(label, content, argument_is_string):
    """
    Generates a string to write it into an HTML file. It is used to specify an option inside the
    dygraphs object.
    :param label: The option's label.
    :param content: The option's content.
    :param argument_is_string: Boolean, whether content should be written with quotation marks, 
    because it is meant as String, or not, because it is meant as a javaScript function.
    :return: The line you can write into an HTML file.
    """
    if argument_is_string:
        return '            ' + label + ': "' + content + '",' + os.linesep
    else:
        return '            ' + label + ': ' + content + ',' + os.linesep


def get_checkbox_id(chart_id, graph_number):
    """
    Generates an simple ID for a checkbox, related on the chart's id, the checkbox belongs to, 
    and a number.
    :param chart_id: A string, containing the chart's id.
    :param graph_number: simple number, representing the graph line, the checkbox belongs to.
    :return: simple ID as String
    """
    return chart_id + constants.CHECKBOX_ID_SPLITTER + str(graph_number)


def get_legend_div_id(chart_id):
    """
    Generates a simple id for a chart legend's div element through adding a string to the chart id.
    :param chart_id: ID of the chart which legend should be carried by the div the ID is for.
    :return: simple ID as String
    """
    return chart_id + '_legend'


def create_buttons(html_document, chart_id):
    """
    Creates two html buttons - 'select all' and 'deselect all' - which allow selecting or 
    deselecting all checkboxes and with this all graph lines of one chart at once.
    :param html_document: The html file, the checkboxes should be written in.   
    :param chart_id: The id of the chart, the checkboxes should belong to.
    :return: None
    """
    html_document.write('<p>' + os.linesep)
    html_document.write('    <button type="button" onclick="selectAll(this, '
                        + chart_id + ', ' + "'" + chart_id + "'" +
                        ')">select all</button>' + os.linesep)
    html_document.write('    <button type="button" onclick="deselectAll(this, '
                        + chart_id + ', ' + "'" + chart_id + "'" +
                        ')">deselect all</button>' + os.linesep)
    html_document.write('</p>' + os.linesep)


def create_checkboxes(html_document, chart_id, graph_identifiers):
    """
    This function creates checkboxes and related labels for each graph line of one chart. The 
    checkboxes allow to select and deselect single graph lines individually. For 
    better readability, they're arranged in an html table.
    :param html_document: The html file, the checkboxes should be written in.   
    :param chart_id: The id of the chart, the checkboxes should belong to.
    :param graph_identifiers: A list which contains the names of all graph lines.
    :return: None
    """
    instance_counter = 0
    html_document.write('<table>' + os.linesep)
    html_document.write('<tr>' + os.linesep)
    for instance in graph_identifiers:

        # for better readability, checkboxes are arranged in a table. Therefore,
        # it needs a linebreak after a view checkboxes:
        if (instance_counter % constants.COLUMN_NUMBER_OF_CHECKBOXES == 0) \
                and instance_counter != 0:
            html_document.write('    </tr>' + os.linesep + '    <tr>' + os.linesep)

        # create html code for checkbox
        html_document.write('        <td><input type=checkbox id="'
                            + get_checkbox_id(chart_id, instance_counter) + '" name="'
                            + chart_id + '" onClick="change(this, '
                            + chart_id + ')" checked>' + os.linesep)
        # create html code for label
        html_document.write('        <label for="' + get_checkbox_id(chart_id,
                                                                     instance_counter) + '">' +
                            instance + '</label></td>' + os.linesep)
        instance_counter += 1
    html_document.write('</tr>' + os.linesep)
    html_document.write('</table>' + os.linesep)


def create_html(html_filepath, csv_files, per_iteration_requests, header, sourcepath):
    """
    Writes an html file which visualizes the contents of csv tables in a nice way.
    :param html_filepath: The path the html file should be saved at.
    :param csv_files: A list of file names from csv tables which should be visualized
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :param header: A list of lists which contains the csv column names to label
    inside the html reasonably
    :param sourcepath: A file path which is used as caption for the resulting html. Should be the
    path of the PerfStat output file.
    :return: None
    """
    titles = util.get_titles(per_iteration_requests)
    chart_ids = util.get_object_ids(per_iteration_requests)
    y_labels = util.get_units(per_iteration_requests)

    # we want to convert b/s into MB/s, so if the unit is b/s, display it as MB/s.
    # Pay attention, that this rename needs to be compatible with the data_collector module,
    # where the affected values should be reduced by the factor 10^6!!!
    for i in range(len(y_labels)):
        if y_labels[i] == 'b/s':
            y_labels[i] = 'MB/s'

    with open(html_filepath, 'w') as html_document:
        # write head
        with open('graph_html_head_template.txt', 'r') as template:
            html_document.writelines(template.readlines())
        template.close()

        # implement checkbox functionality and legend formatter in javaScript
        html_document.write('<script>' + os.linesep)
        html_document.write('    function change(el, chart) {' + os.linesep)
        html_document.write('        chart.setVisibility(translateNumber(el.id), el.checked);' +
                            os.linesep)
        html_document.write('    }' + os.linesep)
        html_document.write('    function translateNumber(id) {' + os.linesep +
                            '        return id.split("' + constants.CHECKBOX_ID_SPLITTER
                            + '")[1];' + os.linesep + '    }')
        html_document.write(constants.SELECT_ALL_FCT)
        html_document.write(constants.DESELECT_ALL_FCT)
        html_document.write(constants.LEGEND_FORMATTER_FCT)
        html_document.write('</script>' + os.linesep)

        # write caption
        html_document.write('    <h2> ' + sourcepath + ' </h2>')

        # write rest of body
        for chart in range(len(csv_files)):
            html_document.write('<div id="' + chart_ids[chart] + '"' + os.linesep)
            html_document.write(style_line())

            # create html div element in which the chart legend should be showed
            html_document.write('<div id="' + get_legend_div_id(chart_ids[chart]) + '" class="'
                                + constants.LEGEND_DIV_CLASS_NAME + '"></div>')

            # create dygraph object in java script, which is responsible for all data visualisation
            html_document.write('<script type="text/javascript">' + os.linesep)
            html_document.write('    ' + chart_ids[chart] + ' = new Dygraph(' + os.linesep)
            html_document.write('        document.getElementById("' + chart_ids[chart] + '"),'
                                                                                         '' +
                                os.linesep)
            html_document.write('        "' + csv_files[chart] + '",' + os.linesep)
            html_document.write('        {' + os.linesep)
            # write options into dygraph object's constructor.
            html_document.write(option_line('xlabel', constants.X_LABEL, True))
            html_document.write(option_line('ylabel', y_labels[chart], True))
            html_document.write(option_line('title', titles[chart], True))
            html_document.write(option_line('legend', 'always', True))
            html_document.write(option_line('labelsDiv', 'document.getElementById("' +
                                            get_legend_div_id(chart_ids[chart]) + '")', False))
            html_document.write(option_line('highlightSeriesOpts', '{strokeWidth: 2}', False))
            html_document.write(option_line('legendFormatter', 'legendFormatter', False))
            html_document.write('        }' + os.linesep + '    );' + os.linesep)
            html_document.write('</script>' + os.linesep)

            # create 'select all' and 'deselect all' buttons
            create_buttons(html_document, chart_ids[chart])

            # create checkboxes
            create_checkboxes(html_document, chart_ids[chart], header[chart])

            # give some space between single charts
            html_document.write('<p/>' + os.linesep)

        # end html document
        html_document.write('</body>' + os.linesep + '</html>')

    html_document.close()
