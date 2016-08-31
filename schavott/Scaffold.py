import sys
import subprocess
import pyfasta
import platform
import os
import shutil


class Scaffold(object):
    """Scaffold genomes wiht SSPACE."""
    def __init__(self, contigPath, path_to_np_reads, scaffolder, output, sspace_path = None):
        self.nrReads = 0
        self.output = output
        self.npReads = path_to_np_reads
        self.scaffoldCounter = 1
        self._set_contigPath(contigPath)
        self.scaffoldApp = scaffolder
        if self.scaffoldApp == 'sspace':
            self.sspacePath = sspace_path
            self._test_sspace(sspace_path)
        elif self.scaffoldApp == 'links':
            self._test_links()
        self._get_N50(self.contigPath)
        self._get_NrContigs(self.contigPath)
        self._contig_size_list(self.contigPath)
        self._contig_size_dict(self.contigPath)

    def run_scaffold(self, passCounter):
        print('In run scaffold')
        if self.scaffoldApp == 'sspace':
            self.run_sspace(passCounter)
        elif self.scaffoldApp == 'links':
            print('In elif links')
            self.run_links(passCounter)

    def run_links(self, passCounter):
        """Run LINKS"""
        print('In run LINKS')
        base_name  = self.output + '_' + str(self.scaffoldCounter)
        self._create_fof()
        bloom_filter_file = self.output + '_1.bloom'
        if self.scaffoldCounter == 1:
            args = ['LINKS', '-f', self.contigPath, '-s', self.fof, '-b', base_name, '-d', '1000', '-k', '10']
        else:
            #Use bloom filter created in the first scaffold attempt. 
            args = ['LINKS', '-f', self.contigPath, '-s', self.fof, '-b', base_name, '-d', '1000', '-k', '10', '-r', bloom_filter_file]

        process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        out, err = process.communicate()
        print(err)
        fasta = base_name  + '.scaffolds.fa'
        print(fasta)
        self.scaffoldCounter += 1
        self.parse_fasta(fasta)
        self.nrReads = passCounter

    def run_sspace(self, passCounter):
        outdir = self.output + '_' + str(self.scaffoldCounter)
        os.mkdir(outdir)
        # Run SSPACE without alignment step
        args = ['perl', self.sspacePath, '-c', self.contigPath,
                '-p', self.npReads, '-i', '70', '-a', '1500', '-g' '-5000',
                '-b', outdir]

        process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        out, err = process.communicate()

        fasta = outdir + '/scaffolds.fasta' 
        self.scaffoldCounter += 1
        self.parse_fasta(fasta)
        self.nrReads = passCounter

    def parse_fasta(self, fasta):
        """Parse resulting fasta file from SSPACE"""
        self._get_N50(fasta)
        self._get_NrContigs(fasta)
        self._contig_size_list(fasta)
        self._contig_size_dict(fasta)

    def _test_sspace(self, path):
        """Test if SSPACE exist"""
        try:
            open(path, 'r')
        except IOError:
            print('Error: ' + str(path) + ' does not appear to exist')
            sys.exit(0)

    def _set_contigPath(self, contigPath):
        """Try to set the path for contig file."""
        try:
            open(contigPath, 'r')
            self.contigPath = contigPath
        except IOError:
            print('Error: ' + str(contigPath) + ' does not appear to exist')
            sys.exit(0)

    def _get_N50(self, path):
        """Calculate N50 value for fasta file."""
        self._contig_size_list(path)

        if len(self.contig_sizes) == 0:
            return 0
        total_bases = sum(self.contig_sizes)
        half_size = total_bases/2
        N50 = 0
        contig_sum = 0
        for contig in self.contig_sizes:
            N50 = contig
            contig_sum += contig
            if contig_sum > half_size:
                break

        self.N50 = N50


    def _get_NrContigs(self, path):
        """Find the number of contigs in the fasta file."""
        f = pyfasta.Fasta(path)
        counter = 0
        for header in f:
            counter += 1
        self.nrContigs = counter


    def _contig_size_dict(self, path):
        """Find the distribution of contig sizes."""
        f = pyfasta.Fasta(path)
        self.contig_size_dict = {}
        for keys in f.keys():
            self.contig_size_dict[keys] = len(f[keys])
        self.contig_size_dict


    def _contig_size_list(self, path):
        """Insert all contig sizes in a list."""
        f = pyfasta.Fasta(path)
        self.contig_sizes = []
        for keys in f.keys():
            self.contig_sizes.append(len(f[keys]))
        self.contig_sizes.sort()

    def _create_fof(self):
        """Create fof-file for links"""
        self.fof = self.output + '.fof'
        path = 'reads_fasta'
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        with open(self.fof, 'w') as fof_file:
            for item in files:
                fof_file.write(path + '/' + item + '\n')

    def _test_links(self):
        """Test LINKS."""
        args = ['LINKS', '-v']
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        