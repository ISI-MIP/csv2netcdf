import numpy as np
import csv
import json
import netCDF4
import argparse
import os

parser = argparse.ArgumentParser(description='Convert CSV files from regional marine-fishery sector to NetCDF.')

parser.add_argument('-b', '--base', dest='basedir',
                    default='/work/bb0820/ISIMIP/ISIMIP3b/UploadArea/marine-fishery_regional',
                    help='base dir to regional models')
parser.add_argument('-m', '--model', dest='model', required=True,
                    help='regional model')
parser.add_argument('-f', '--first-file', dest='first_file', action='store_true',
                    help='only process first file found')

args = parser.parse_args()
ref_year = 1601

# extract variable meta data from ISIMIP3 protocol
def get_protocol_data(variable,data):
    with open('isimip-protocol-3/definitions/variable.json') as json_file:
        protocol_data = json.load(json_file)
        if any(tag['specifier'] == variable for tag in protocol_data):
            for var in protocol_data:
                if var['specifier'] == variable:
                    return(var[data])
        else:
            return(None)


# read contact information from contacts.json
def get_contact_data(model,region):
    with open('contacts.json') as json_file:
        contacts_data = json.load(json_file)
        return [contacts_data[model]['contact'][region], contacts_data[model]['institution'][region]]


for root, dirs, files in os.walk(args.basedir + '/' + args.model + '/convert2nc/csv', topdown=False):
    for name in sorted(files):
        if name.endswith('csv'):
            print('Converting : ' + os.path.join(root, name))

            # extract specifiers from file name
            variable = name.split(sep='_')[6]
            model = name.split(sep='_')[0]
            region = name.split(sep='_')[7]
            time_res = name.split(sep='_')[8]
            year_first = int(name.split(sep='_')[9])
            year_last = int(os.path.splitext(name)[0].split(sep='_')[10])

            # get variable metadta
            try:
                units = get_protocol_data(variable,'units')
                long_name = get_protocol_data(variable,'long_name')
                if units is None or long_name is None:
                    print('ERROR : variable not defined in protocol. Quit.')
                    quit()
            except ValueError:
                print('ERROR : could not read variable details from protocol. Quit.')

            times = []
            bins = []
            values = []

            # read csv file
            f = open(os.path.join(root, name), 'r').readlines()

            # read time axis and data
            if model == "mizer" and region == "east-bering-sea":
                column_offset = 1
            else:
                column_offset = 0
            if variable in ['tcblog10', 'tclog10']:
                column_offset_values = column_offset + 1
            else:
                column_offset_values = column_offset

            for line in f[1:]:
                fields = line.split(',')
                times.append(int(fields[column_offset].replace('"', '')))
                if variable in ['tcblog10', 'tclog10']:
                    bins.append(float(fields[column_offset_values].replace('"', '')))
                values.append(float(fields[1 + column_offset_values].replace('"', '')))

            # prepare output file
            ncout = netCDF4.Dataset(os.path.join(root.replace("/csv", "/netcdf"), os.path.splitext(name)[0] + '.nc'), 'w',format='NETCDF4_CLASSIC')
            ncout.createDimension('time', len(set(times)))
            if variable in ['tcblog10', 'tclog10']:
                ncout.createDimension('bins', 6)
            ncout.createDimension('lon', 1)
            ncout.createDimension('lat', 1)

            # fill file
            time = ncout.createVariable('time',np.dtype('float32').char,('time'))
            if variable in ['tcblog10', 'tclog10']:
                bins_nc = ncout.createVariable('bins',np.dtype('float32').char,('bins'))
            lat = ncout.createVariable('lat',np.dtype('float32').char,('lat'))
            lon = ncout.createVariable('lon',np.dtype('float32').char,('lon'))

            if time_res == 'annual':
                time.units = 'years since ' + str(ref_year) + '-01-01 00:00:00'
                time_factor = 1
            elif time_res == 'monthly':
                time.units = 'months since ' + str(ref_year) + '-01-01 00:00:00'
                time_factor = 12

            time_index_first = time_factor * (year_first - ref_year)
            time_index_last  = time_factor * (year_last  - ref_year + 1)

            if len(set(times)) != (time_index_last - time_index_first):
                print('ERROR : internal number of time steps don\'t match expected numbers from file name specifiers. Quit')
                quit()

            time.standard_name = 'time'
            time.long_name = 'Time'
            time.axis = 'T'
            time.calendar = '360_day'
            time[:] = range(time_index_first, time_index_last)

            lat.long_name = 'Latitude'
            lat.standard_name = 'latitude'
            lat.units = 'degrees_north'
            lat.axis = 'Y'
            lat[:] = 0.0

            lon.long_name = 'Longitude'
            lon.standard_name = 'longitude'
            lon.units = 'degrees_east'
            lon.axis = 'X'
            lon[:] = 0.0


            if variable in ['tcblog10', 'tclog10']:
                bins_nc[:] = range(1, 7)
                bins_nc.long_name = 'log10 Weight Bins'
                bins_nc.standard_name = 'log10_weight_bins'
                bins_nc.units = '-'
                bins_nc.axis = 'Z'
                bins_nc.comment = 'log 10 weight bins as defined per simulation protocol: 1-10g, 10-100g, 100g-1kg, 1-10kg, 10-100kg, >100kg'
                var = ncout.createVariable(variable,np.dtype('float32').char,('time','bins','lat','lon'), zlib=True, complevel=5, fill_value=1e+20)
                var[:] = [values[i::len(set(times))] for i in range(len(set(times)))]
            else:
                var = ncout.createVariable(variable,np.dtype('float32').char,('time','lat','lon'), zlib=True, complevel=5, fill_value=1e+20)
                var[:] = values[:]

            var.missing_value = 1e+20
            var.long_name = long_name
            var.units = units


            # set global attributes contact and institution from contacts.json
            ncout.contact = get_contact_data(model,region)[0]
            ncout.institution = get_contact_data(model,region)[1]

            ncout.close()

            if args.first_file:
                quit()
