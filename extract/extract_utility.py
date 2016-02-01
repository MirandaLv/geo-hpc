"""Contains ExtractObject, ValidateObject, MergeObject classes and related functions"""

import sys
import os
import time
from numpy import isnan

# import rasterstats as rs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_rasterstats as rs

import pandas as pd

# from rpy2.robjects.packages import importr
# from rpy2 import robjects

# import subprocess as sp


def str_to_range(value):
    """Set 

    Args:
        value (str): x
    """
    if not isinstance(value, str):
        raise Exception("str_to_range: input must be str")

    range_split = value.split(':')

    if len(range_split) != 2:
        raise Exception("str_to_range: result of split must be 2 items")

    try:
        start = int(range_split[0])
        end = int(range_split[1]) + 1
    except:
        raise Exception("str_to_range: invalid years")

    return range(start, end)


def parse_year_string(value):
    """Set 

    Args:
        value (str): x
    """           
    statements = [x for x in str(value).split('|') if x != ""]

    tmp_years = []

    for i in statements:
        if i.startswith('!'):

            if ':' in i:
                tmp_range = str_to_range(i[1:])
                tmp_years = [y for y in tmp_years if y not in tmp_range] 
            else:
                try:
                    year = int(i[1:])
                except:
                    raise Exception("parse_year_string: invalid year")

                tmp_years = [y for y in tmp_years if y != year]
        else:

            if ':' in i:
                tmp_range = str_to_range(i)
                tmp_years += tmp_range
            else:
                try:
                    year = int(i)
                except:
                    raise Exception("parse_year_string: invalid year")

                tmp_years += [year]


    return map(str, tmp_years)


class ExtractObject():
    """Contains variables and functions needed to validate and run extracts.

    Attributes:

        _extract_method (str): x

        _vector_extensions (List[str]): x
        _vector_path (str): x
        _vector_extension (str): x
        _vector_info (Tuple(str, str)): x
        _r_vector : x

        _extract_options (dict): x
        _extract_type (str): x

        _base_path (str): x

        default_years (List[int]): x
        _years (List[str]): x

        _file_mask (str): x
        _run_option (str): x

        _raster_extensions (List[str]): x

        _raster_path (str): x

    """

    def __init__(self, builder=False):

        self._builder = builder

        self._extract_method = None

        # accepted vector file extensions
        self._vector_extensions = [".geojson", ".shp"]

        self._vector_path = None
        self._vector_extension = None
        self._vector_info = (None, None)
        # self._r_vector = None

        # available extract types and associated identifiers
        self._extract_options = {
            # "var": "v",
            # "std": "d",
            "sum": "s",
            "max": "x",
            # "min": "m",
            "mean": "e"
        }
        self._extract_type = None
        
        self._base_path = None

        # self.default_years = range(1000, 10000)
        self._years = []

        self._file_mask = None
        self._run_option = None


        # accepted raster file extensions
        self._raster_extensions = [".tif", ".asc"]

        # self._raster_path = None


    def set_extract_method(self, value):
        """Set 

        Args:
            value (str): x
        """
        # run init for specified extract method

        if value == "python":
            self._init_python()
        # elif value == "rpy2":
        #     self._init_rpy2()
        # elif value == "rscript":
        #     self._init_rscript()
        else:
            raise Exception("invalid extract method (" + value + ")")

        self._extract_method = value


    # load packages and init for specified extract method
    def _init_python(self):
        tmp_init = 1
    #     # import rasterstats as rs
    #     sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    #     import rasterstats.main as rs


    # def _init_rpy2(self):
    #     # from rpy2.robjects.packages import importr
    #     # from rpy2 import robjects
        
    #     # try loading rpy2 packages, open vector file and other init
    #     try:
    #         # load packages
    #         self.__rlib_rgdal = importr("rgdal")
    #         self.__rlib_raster = importr("raster")

    #         # list of valid extract types with r functions
    #         self.__extract_funcs = {
    #             "sum": robjects.r.sum,
    #             "max": robjects.r.max,
    #             "mean": robjects.r.mean
    #         }

    #         self._set_r_vector()

    #     except:
    #         raise Exception("rpy2 initialization failed")


    # def _init_rscript(self):
    #     tmp_init = 1
    # #     import subprocess as sp


    # def _set_r_vector(self):
    #     """Set _r_vector attribute.

    #     Makes sure extract method is rpy2 and vector info has 
    #     been set, then sets _r_vector.
    #     """
    #     if not self._builder and self._extract_method == "rpy2" and self._vector_info != (None, None):
    #         self._r_vector = self.__rlib_rgdal.readOGR(self._vector_info[0], self._vector_info[1])


    def set_vector_path(self, value):
        """Set 

        should this have more advanced vector checks? (ie load and test)

        Args:
            value (str): x
        """
        if self._extract_method == None:
            raise Exception("set_vector_path: no extract method set") 

        if not os.path.isfile(value):
            raise Exception("set_vector_path: vector does not exist (" + value + ")")
   
        self._vector_path = value
        self._set_vector_extension(value)

        vector_dirname = os.path.dirname(value)
        vector_filename, self._vector_extension = os.path.splitext(os.path.basename(value))

        # break vector down into path and layer
        # different for shapefiles and geojsons
        if self._vector_extension == ".geojson":
            self._vector_info = (value, "OGRGeoJSON")

        elif self._vector_extension == ".shp":
            self._vector_info = (vector_dirname, vector_filename)

        else:
            raise Exception("invalid vector extension (" + self._vector_extension + ")")

        # self._set_r_vector()


    def _set_vector_extension(self, value):
        """Set 

        Args:
            value (str): x
        """
         # check extension
        if not value.endswith(tuple(self._vector_extensions)):
            raise Exception("invalid vector extension (" + value + ")")

        self._vector_extension = value


    def _check_file_mask(self):
        """Run general validation of file_mask based on base_path

        Makes sure that:
        1) temporally invariant file masks (ie "None") are not used with 
        a base path that indicates temporal data (ie base_path is directory)
        2) temporal file masks (ie not "None") are not used with a base path that 
        indicates temporally invariant data (ie base_path is file)
        """
        if self._file_mask == "None" and self._base_path != None and not self._base_path.endswith(tuple(self._raster_extensions)):
            raise Exception("check_file_mask: invalid use of None file_mask based on base_path")
        elif self._file_mask not in [None, "None"] and self._base_path != None and self._base_path.endswith(tuple(self._raster_extensions)):
            raise Exception("check_file_mask: invalid use of temporal file_mask based on base_path")


    def set_base_path(self, value):
        """Set 

        Args:
            value (str): base path where year/day directories for processed data are located
        """
        # validate base_path
        if not os.path.exists(value):
            raise Exception("base_path is not valid ("+ value +")")

        self._base_path = value

        self._check_file_mask()


    def set_years(self, value):
        """Set 

        Args:
            value (str): x
        """
        statements = [x for x in str(value).split('|') if x != ""]
        
        if len(statements) == 0:
            self._years = map(str, range(1000,10000))

        else:
            self._years = parse_year_string(value)


    def set_file_mask(self, value):
        """Test

        Args:
            value (str): x
        """
        if value == "None":

            tmp_run_option = 1

        elif "YYYY" in value:

            if "MM" in value and not "DDD" in value:
                tmp_run_option = 3
            elif "DDD" in value and not "MM" in value:
                tmp_run_option = 4
            elif not "MM" in value and not "DDD" in value:
                tmp_run_option = 2
            else:
                raise Exception("set_file_mask: ambiguous temporal string ("+str(value)+")")

        else:
            raise Exception("set_file_mask: invalid file mask ("+str(value)+")")


        self._file_mask = value
        self._run_option = str(tmp_run_option)
        self._check_file_mask()


    def set_extract_type(self, value):
        """Set 

        Args:
            value (str): x
        """
        # validate input extract type
        if value not in self._extract_options.keys():
            raise Exception("invalid extract type ("+ value +")")

        self._extract_type = str(value)


    def gen_data_list(self):
        """Set 

        should this have more advanced raster checks? (ie load and test)

        Args:
            value (str): x
        """
        # temporally invariant dataset
        if self._run_option == "1":

            qlist = [[['',''], self._base_path]]


        # year
        elif self._run_option == "2":

            id_char = "Y"

            qlist = [
                        [["".join([x for x,y in zip(name, self._file_mask) if y == id_char and x.isdigit()])], name] 
                        for name in os.listdir(self._base_path) 
                        if not os.path.isdir(os.path.join(self._base_path, name)) 
                        and name.endswith(tuple(self._raster_extensions)) 
                        and "".join([x for x,y in zip(name, self._file_mask) if y == id_char and x.isdigit()]) in self._years
                    ]


        # year month/day
        elif self._run_option in ["3", "4"]:

            if self._run_option == "3":
                # year month
                id_char = "M"
            else:
                # year day
                id_char = "D"   


            years = [
                        name 
                        for name in os.listdir(self._base_path) 
                        if os.path.isdir(os.path.join(self._base_path, name)) 
                        and name in self._years
                    ]

            # list of all [[year, month], name] combos
            qlist = []

            for year in years:
                path_year = self._base_path +"/"+ year
                qlist += [
                            [[year, "".join([x for x,y in zip(year+"/"+name, self._file_mask) if y == id_char and x.isdigit()])], year+"/"+name] 
                            for name in os.listdir(path_year) 
                            if not os.path.isdir(os.path.join(path_year, name)) 
                            and name.endswith(tuple(self._raster_extensions))
                        ]


        else:
            raise Exception("Invalid run_option value: " + str(self._run_option))


        # if len(qlist) == 0:
        #     raise Exception("No rasters found based on input parameters")


        # sort qlist
        qlist = sorted(qlist)

        return qlist


    # def set_raster_extension(self, value):
    #     """Set 

    #     Args:
    #         value (str): 
    #     """

    
    # --------------------------------------------------------------------
    # --------------------------------------------------------------------


    # run proper extract based on extract method
    def run_extract(self, in_raster, in_output):
        """Set 

        Args:
            (): x
        """        
        # make sure all options are set
        # 

        # print "running extract: " + in_output

        if self._extract_method == "python":
            return self._python_extract(in_raster, in_output)

        # elif self._extract_method == "rscript":
        #     return self._rscript_extract(in_raster, in_output)

        # elif self._extract_method == "rpy2":
        #     return self._rpy2_extract(in_raster, in_output)



    # run extract user rasterstats
    def _python_extract(self, raster, output):
        """Set 

        Args:
            (): x
        """
        # try:
        Te_start = int(time.time())

        stats = rs.zonal_stats(self._vector_path, raster, stats=self._extract_type, all_touched=True, weights=True, geojson_out=True)

        # except:
        #     print "error with python_extract: " + output

        #     if os.path.isfile(output+".csv"):
        #         os.remove(output+".csv")

        #     return False


        # # try:
        # for i in stats:
        #     i["ad_extract"] = i.pop(self._extract_type)
        #     try:
        #         if isnan(i["ad_extract"]):
        #             i["ad_extract"] = "NA"
        #     except:
        #         i["ad_extract"] = "NA"

        
        # out = open(output+".csv", "w")
        # out.write(rs.utils.stats_to_csv(stats))


        tmp_data = [i['properties'] for i in stats]

        tmp_df = pd.DataFrame(tmp_data)
        tmp_df.rename(columns = {self._extract_type:'ad_extract'}, inplace=True)
        tmp_df['ad_extract'].fillna('NA', inplace=True)
        tmp_df.to_csv(output+".csv", sep=",", encoding="utf-8", index=False)


        Te_run = int(time.time() - Te_start)

        return (0, 'completed extract ('+ output +') in '+ str(Te_run) +' seconds')


    # !!! WARNING !!!
    # Last time I tested this rpy2 was not running properly.
    # Not sure if it was an issue running (no errors popped) or writing to csv.
    # Did not look into it since we are switching over to full python for extracts.
    # !!! WARNING !!!
    # # run extract using rpy2
    # def _rpy2_extract(self, raster, output):
    #     """Set 

    #     Args:
    #         (): x
    #     """
    #     try:
    #         # open raster
    #         r_raster = self.__rlib_raster.raster(raster)

    #         # *** need to implement different kwargs based on extract type ***
    #         if self._extract_type == "mean":
    #             kwargs = {"fun":__extract_funcs[self._extract_type], "sp":True, "na.rm":True, "weights":True, "small":True}
    #         else:
    #             kwargs = {"fun":__extract_funcs[self._extract_type], "sp":True, "na.rm":True}

    #         Te_start = int(time.time())

    #         robjects.r.assign('r_extract', self.__rlib_raster.extract(r_raster, self._r_vector, **kwargs))

    #         Te_run = int(time.time() - Te_start)
    #         print 'extract ('+ output +') completed in '+ str(Te_run) +' seconds'


    #         robjects.r.assign('r_output', output+".csv")

    #         robjects.r('colnames(r_extract@data)[length(colnames(r_extract@data))] <- "ad_extract"')
    #         robjects.r('write.table(r_extract@data, r_output, quote=T, row.names=F, sep=",")')
            
    #         return 0, None

    #     except:
    #         return 1, "Rpy2 extract failed"


    # # run R extract script using subprocess call
    # def _rscript_extract(self, raster, output):
    #     """Set 

    #     Args:
    #         (): x
    #     """
    #     try:  

    #         # buildt command for Rscript
    #         cmd = "Rscript extract.R " + self._vector_info[0] +" "+ self._vector_info[1] +" "+ raster +" "+ output +" "+ self._extract_type
    #         print cmd

    #         # spawn new process for Rscript
    #         sts = sp.check_output(cmd, stderr=sp.STDOUT, shell=True)
    #         print sts
    #          return  0, None

    #     except sp.CalledProcessError as sts_err:                                                                                                   
    #         print ">> subprocess error code:", sts_err.returncode, '\n', sts_err.output
    #         return 1, "Rscript extract failed"



class ValidateObject():
    """Contains variables and functions needed to validate results of an extract job.

    Make sure everything all extracts that were expected to be run for a job
    were actually run and completed.

    Attributes:

        _something1 (str): x

        _something2 (List[str]): x


    """

    def __init__(self, interface=False):

        self._interface = interface



class MergeObject():
    """Contains variables and functions needed to merge results of an extract job.

    Merges all available extracts results given boundary, dataset, extract type and year string.
    Does not perform source data checks (see ExtractObject) or job validation (see ValidateObject).

    When run as part of job chain (ie: Extract > Validate > Merge) users can confirm via ExtractObject and ValidateObject
    that all available datasets meeting job config specification were extracted and thus will be merged.

    When running merge on its own, only available extracts are used (ie: we do not check if there is some dataset that 
    exists, but has not yet been extracted)

    Attributes:

        _years
        _merge_data


        ---------------------------------------------------

        base_path (str): x
        bnd_name (str): x
        year_string (str): x

        merge input object (from json or other) uses same format as job json "defaults" and "data"
        
        depends on datasets json as well

        defaults:
            bnd_name
            extract_type
            output_base
            years

        dataset_list

        dataset specific:
            dataset name
            anything from defaults

        merge output base (csv for each bnd)

    """

    def __init__(self, merge_json, merge_output_dir, interface=False):

        # merge_path = os.path.abspath(merge_path)

        # merge_file = open(merge_path, 'r')
        # merge_json = json.load(merge_file)
        # merge_file.close()


        self.interface = interface
        
        self.merge_output_dir = os.path.abspath(merge_output_dir)


        self._years = None

        required_options = ["bnd_name", "extract_type", "output_base", "years"]
        missing_defaults = [i for i in required_options if i not in merge_json['defaults'].keys()]

        if len(missing_defaults) > 0:
            print "MergeObject warning: required option(s) missing from defaults ("+str(missing_defaults)+")"


        self._merge_data = []

        for dataset_options in merge_json['data']:

            dataset_name = dataset_options['name']
            print dataset_name

            tmp_config = {}
            tmp_config['name'] = dataset_name

            for k in required_options:
                if k in dataset_options:
                    tmp_config[k] = dataset_options[k]
                else:
                    tmp_config[k] = merge_json['defaults'][k]
            

            self._merge_data.append(tmp_config)


    def build_merges(self):
        """build_merges 

        """
        # Ts = int(time.time())

        bnd_list = set([i['bnd_name'] for i in self._merge_data])

        for bnd_name in bnd_list:
            
            print "Starting merge process for bnd_name = " + bnd_name

            if self.interface == True:

                # ask for path
                # make sure directory exists
                # make sure file name ends with .csv

                while True:
                    sys.stdout.write("Absolute file path for output? \n> ")
                    answer = raw_input().lower()

                    if os.path.isdir(os.path.dirname(answer)):
                        if answer.endswith(".csv"):
                            merge_output_csv = answer
                            break
                        else:
                            sys.stdout.write("Invalid file extension (must end with \".csv\").\n")

                    else:
                        sys.stdout.write("Directory specified does not exist.\n")



                # merge_output_csv =  self.merge_output_dir + "/merge_" + bnd_name + ".csv"

            else:
                merge_output_csv =  self.merge_output_dir + "/merge_" + bnd_name + ".csv"

            # if interface ask for output path
            # 

            merge = 0

            for i in self._merge_data:
                if i['bnd_name'] == bnd_name:

                    self.set_years(i['years'])

                    data_name = i['name']
                    extract_type = i['extract_type']
                    extract_base = i['output_base']

                    # --------------------------------------------------
                    extract_dir = extract_base + "/" + bnd_name + "/cache/" + data_name +"/"+ extract_type 

                    print "\tChecking for extracts in: " + extract_dir

                    # validate inputs by checking directories exist
                    if not os.path.isdir(extract_base):
                        sys.exit("Directory for extracts does not exist. You may not be connected to sciclone ("+extract_base+")")
                    elif not os.path.isdir(extract_base + "/" + bnd_name):
                        sys.exit("Directory for specified bnd_name does not exist (bnd_name: "+bnd_name+")")
                    elif not os.path.isdir(extract_base + "/" + bnd_name + "/cache/" + data_name):
                        sys.exit("Directory for specified dataset does not exists (data_name: "+data_name+")")
                    elif not os.path.isdir(extract_dir):
                        sys.exit("Directory for specified extract type does not exist (extract_type: "+extract_type+")")
                        # print "\tWarning: extract type \"" + extract_type + "\" not found for " + data_name
                        # continue


                    # find and sort all relevant extract files
                    rlist = [fname for fname in os.listdir(extract_dir) if (len(fname) == 10 or fname[5:9] in self._years) and os.path.isfile(extract_dir +"/"+ fname) and fname.endswith(".csv")]
                    rlist = sorted(rlist)

                    # exit if no extracts found
                    if len(rlist) == 0:
                        print "\tWarning: no extracts found for: " + extract_dir
                        continue
                    

                    print "\tMerging extracts: " + extract_dir

                    for item in rlist:

                        result_csv = extract_dir +"/"+ item
                        
                        result_df = pd.read_csv(result_csv, quotechar='\"', na_values='', keep_default_na=False)

                        if not isinstance(merge, pd.DataFrame):
                            merge = result_df.copy(deep=True)
                            merge.rename(columns={"ad_extract": item[:-4]}, inplace=True)

                        else:
                            merge[item[:-4]] = result_df["ad_extract"]



            if isinstance(merge, pd.DataFrame):

                merge.to_csv(merge_output_csv, index=False)

                print '\tMerge completed for ' + bnd_name
                print '\tResults output to ' + merge_output_csv

            else:
                print '\tWarning: no extracts merged for bnd_name = ' + bnd_name


        # T_run = int(time.time() - Ts)
        # print 'Merge Runtime: ' + str(T_run//60) +'m '+ str(int(T_run%60)) +'s'


    def set_years(self, value):
        """Set 

        Args:
            value (str): x
        """
        statements = [x for x in str(value).split('|') if x != ""]
        
        if len(statements) == 0:
            self._years = map(str, range(1000,10000))

        else:
            self._years = parse_year_string(value)


