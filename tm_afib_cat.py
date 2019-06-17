import os, csv, glob, datetime

# set working dir
os.chdir('/gscmnt/gc2783/qc/topmed_assay/')

# set date
mm_dd_yy = datetime.datetime.now().strftime("%m%d%y")

# create status header field list
ccdg_qc_outfile_header = ['QC Sample', 'WOID', 'PSE', 'Launch Status', 'Launch Date', 'Instrument Check',
                          '# of Inputs','# of Instrument Data', 'QC Status', 'QC Date', 'QC Failed Metrics',
                          'COD Collaborator', 'QC Directory', 'Top Up']


# cat files together
def file_cat(infile, outfile, header=''):
    file_exits = os.path.isfile(outfile)
    with open(infile, 'r') as infilecsv, open(outfile, 'a') as outfilecsv:
        # read infile, either use header= or take header from file
        infile_reader = csv.DictReader(infilecsv, delimiter='\t')
        if not header:
            infile_header = infile_reader.fieldnames
        else:
            infile_header = header
        # set outfile writer object, write header if first pass through
        outfile_writer = csv.DictWriter(outfilecsv, fieldnames=infile_header, delimiter='\t',extrasaction='ignore')
        if not file_exits:
            outfile_writer.writeheader()
        # write to files if line populated in file with 'and condition', else write all lines.
        if 'QC Sample' in infile_header:
            for line in infile_reader:
                if line['QC Sample'] and line['Launch Status']:
                    outfile_writer.writerow(line)
        else:
            for line in infile_reader:
                outfile_writer.writerow(line)
    return


# create woid list, eliminate any glob matches with letters
def woid_list():
    woid_dirs = []

    def is_int(string):
        try:
            int(string)
        except ValueError:
            return False
        else:
            return True
    woid_dir_unfiltered = glob.glob('285*')
    for woid in filter(is_int, woid_dir_unfiltered):
        woid_dirs.append(woid)

    return woid_dirs


# get woids
woid_dir_list = woid_list()

# file glob lists
ccdg_qc_status_files = []
ccdg_qc_all_files = []
qc_instrument_fail_files = []
qc_status_active_fail_files = []
analysis_qc_all_files = []

for woid in woid_dir_list:
    ccdg_qc_status_files.append(glob.glob(woid + '/285*.qcstatus.tsv'))
    ccdg_qc_all_files.append(glob.glob(woid + '/qc.*/attachments/*all*'))
    qc_instrument_fail_files.append(glob.glob(woid + '/*launch.fail.tsv'))
    qc_status_active_fail_files.append(glob.glob(woid + '/*instrument.pass.status.active.tsv'))
    if not os.path.isfile(woid + '/' + woid + '.qcstatus.tsv'):
        analysis_qc_all_files.append(glob.glob(woid + '/qc.*/attachments/*all*'))


# QC STATUS FILE - master sample sheet status file
# status outfile
status_outfile = 'afib.sample.qcstatus.' + mm_dd_yy + '.tsv'
# remove file if already exists so not appending duplicate sample info
if os.path.isfile(status_outfile):
    os.remove(status_outfile)
# cat status files with file_cat method
for file in ccdg_qc_status_files:
    for qc_status_file in file:
        file_cat(infile=qc_status_file, outfile=status_outfile, header=ccdg_qc_outfile_header)

# QC ALL FILE - all samples from all qc file in all woid attachment dirs
qc_all_outfile = 'afib.qc.all.' + mm_dd_yy + '.tsv'
# remove file if already exists so not appending duplicate sample info
if os.path.isfile(qc_all_outfile):
    os.remove(qc_all_outfile)
# cat qc all files with file_cat method
for file in ccdg_qc_all_files:
    for qc_all_file in file:
        file_cat(infile=qc_all_file, outfile=qc_all_outfile)

# QC FAIL FILE - all samples that failed instrument check
qc_fail_outfile = 'afib.launch.fail.' + mm_dd_yy + '.tsv'
# remove file if already exists so not appending duplicate sample info
if os.path.isfile(qc_fail_outfile):
    os.remove(qc_fail_outfile)
# cat all qc files with file cat method
for file in qc_instrument_fail_files:
    for qc_fail_file in file:
        file_cat(qc_fail_file, qc_fail_outfile, header=ccdg_qc_outfile_header)

# QC instrument pass, status active, fails
qc_status_active_outfile = 'afib.cw.active.' + mm_dd_yy + '.tsv'
# remove file if already exists so not appending duplicate sample info
if os.path.isfile(qc_status_active_outfile):
    os.remove(qc_status_active_outfile)
# cat all qc files with file cat method
for file in qc_status_active_fail_files:
    for qc_status_active_file in file:
        file_cat(qc_status_active_file, qc_status_active_outfile, header=ccdg_qc_outfile_header)

# QC analysis top up samples - topup and analysis samples
qc_analysis_all_outfile = 'afib.cgup.qc.all.' + mm_dd_yy + '.tsv'
# remove file if already exists so not appending duplicate sample info
if os.path.isfile(qc_analysis_all_outfile):
    os.remove(qc_analysis_all_outfile)
# cat all analysis qc all files with file cat method
for file in analysis_qc_all_files:
    for qc_analysis_all_file in file:
        file_cat(qc_analysis_all_file, qc_analysis_all_outfile)

# filter duplicates out of status_outfile (take dup with higher value), write uniqu samples to outfile
# write both dup sample to dup outfile
remove_dup_all_outfile = 'afib.qc.all.unique.' + mm_dd_yy + '.tsv'
duplicate_sample_outfile = 'afib.qc.all.duplicates.' + mm_dd_yy + '.tsv'
with open(qc_all_outfile, 'r') as allcsv, open(remove_dup_all_outfile, 'w') as alloutfilecsv, \
        open(duplicate_sample_outfile, 'w') as dupcsv:

    all_outfile_reader = csv.DictReader(allcsv, delimiter='\t')
    status_outfile_header = all_outfile_reader.fieldnames

    all_outfile_writer = csv.DictWriter(alloutfilecsv, fieldnames=status_outfile_header, delimiter='\t')
    all_outfile_writer.writeheader()

    dup_outfile_writer = csv.DictWriter(dupcsv, fieldnames=status_outfile_header, delimiter='\t')
    dup_outfile_writer.writeheader()

    uniq_sample_dict = {}
    all_samples_dict = {}
    results = {}
    duplicate_samples = {}
    count = 0

    for line in all_outfile_reader:
        count += 1
        # populate all_samples_dict using counter as a unique key
        all_samples_dict[count] = line
        # if sample is in results, check if dup has higher instrument count or not, keep higher inst count
        if line['DNA'] in uniq_sample_dict:
            # keep track of duplicates
            duplicate_samples[line['DNA']] = line['DNA']
            if line['instrument_data_count'] > uniq_sample_dict[line['DNA']]:
                # update unique and results dicts
                uniq_sample_dict[line['DNA']] = line['instrument_data_count']
                results[line['DNA']] = line
        else:
            # populate dicts with unique samples
            uniq_sample_dict[line['DNA']] = line['instrument_data_count']
            results[line['DNA']] = line

    # write unique sample list to outfile
    for line in results:
        all_outfile_writer.writerow(results[line])

    # use duplicate_sample dict and all_samples_dict to write all dups to file
    for sample in duplicate_samples:
        for line in all_samples_dict:
            if sample in all_samples_dict[line]['DNA']:
                dup_outfile_writer.writerow(all_samples_dict[line])


