"""
Is responsible to write a html file containing the required charts.
"""
import constants
import util
import os


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
    width_px = None
    height_px = None

    if width_px is None:
        width_px = 500
    if height_px is None:
        height_px = 300
    return '     style="width: ' + str(width_px) + 'px; height: ' + str(height_px) + \
           'px;"></div>' + os.linesep


def option_line(label, content):
    """
    Generates a string to write it into an HTML file. It is used to specify an option inside the
    dygraphs object.
    :param label: The option's label.
    :param content: The option's content.
    :return: The line you can write into an HTML file.
    """
    return '            ' + label + ': "' + content + '",' + os.linesep


def get_checkbox_id(chart_number, instance_number):
    """
    Generates an simple ID for a checkbox relating on two numbers marking iteration and instance
    of the graph line, the checkbox is related on.
    :param chart_number: number of chart
    :param instance_number: number of instance
    :return: simple ID as String
    """
    return str(chart_number) + '_' + str(instance_number)


def create_html(html_filepath, csv_files, search_requests, header, sourcepath):
    """
    Writes an html file which visualizes the contents of csv tables in a proper way.
    :param html_filepath: The path the html file should be saved at.
    :param csv_files: A list of file names from csv tables which should be visualized
    :param search_requests: An OrderedDict of lists which contains all requested object types
    mapped to the corresponding aspects and units which the tool should visualize.
    :param header: A list of lists which contains the csv column names to label
    inside the html reasonably
    :param sourcepath: A file path which is used as caption for the resulting html. Should be the
    path of the PerfStat output path.
    :return: None
    """
    titles = util.get_titles(search_requests)
    object_ids = util.get_object_ids(search_requests)
    y_labels = util.get_units(search_requests)

    with open(html_filepath, 'w') as graphs:

        # write head
        with open('graph_html_head_template.txt', 'r') as template:
            graphs.writelines(template.readlines())
        template.close()

        # write caption
        graphs.write('    <h2> ' + sourcepath + ' </h2>')

        # write rest of body
        chart_counter = 0
        for chart in range(len(csv_files)):
            graphs.write('<div id="' + object_ids[chart] + '"' + os.linesep)
            graphs.write(style_line())
            graphs.write('<p>' + os.linesep)
            graphs.write('    <button type="button" onclick="selectAll(this, '
                         + object_ids[chart] + ', ' + "'" + object_ids[chart] + "'" +
                         ')">select all</button>' + os.linesep)
            graphs.write('    <button type="button" onclick="deselectAll(this, '
                         + object_ids[chart] + ', ' + "'" + object_ids[chart] + "'" +
                         ')">deselect all</button>' + os.linesep)
            graphs.write('</p>' + os.linesep)
            graphs.write('<p>' + os.linesep)
            instance_counter = 0

            for instance in header[chart]:
                graphs.write('    <input type=checkbox id="'
                             + get_checkbox_id(chart_counter, instance_counter) + '" name="'
                             + object_ids[chart] + '" onClick="change(this, '
                             + object_ids[chart] + ')" checked>' + os.linesep)
                graphs.write(
                    '    <label for="' + get_checkbox_id(chart_counter, instance_counter) + '">' +
                    instance + '</label>' + os.linesep)
                instance_counter += 1

            graphs.write('</p>' + os.linesep)
            graphs.write('<script type="text/javascript">' + os.linesep)
            graphs.write('    ' + object_ids[chart] + ' = new Dygraph(' + os.linesep)
            graphs.write('        document.getElementById("' + object_ids[chart] + '"),'
                                                                                   '' + os.linesep)
            graphs.write('        "' + csv_files[chart] + '",' + os.linesep)
            graphs.write('        {' + os.linesep)
            graphs.write(option_line('xlabel', constants.X_LABEL))
            graphs.write(option_line('ylabel', y_labels[chart]))
            graphs.write(option_line('title', titles[chart]))
            graphs.write('        }' + os.linesep + '    );' + os.linesep)
            graphs.write('</script>' + os.linesep)
            chart_counter += 1

        graphs.write('<script>' + os.linesep)
        graphs.write('    function change(el, chart) {' + os.linesep)
        graphs.write('        chart.setVisibility(translateNumber(el.id), el.checked);' +
                     os.linesep)
        graphs.write('    }' + os.linesep)
        graphs.write('    function translateNumber(id) {' + os.linesep +
                     '        return id.split("_")[1];' + os.linesep + '    }')
        graphs.write(constants.SELECT_ALL_FCT)
        graphs.write(constants.DESELECT_ALL_FCT)
        graphs.write('</script>' + os.linesep)
        graphs.write('</body>' + os.linesep + '</html>')

    graphs.close()
