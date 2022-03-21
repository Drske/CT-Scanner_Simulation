import os

IMG_HEIGHT = "5"
TEX_DIRECTORY = "Assets/CT_ScoutView_large_report"

def generate_tex_part(input_img_path, output_img_path, caption):

    return """\\begin{figure}[H]
    \centering
    \subfloat[Original]{
        \includegraphics[height=%scm]{%s/%s}
    }
    \subfloat[Computed]{
        \includegraphics[height=%scm]{%s/%s}
    }
    \caption{%s}
\end{figure}
    """ % (IMG_HEIGHT, TEX_DIRECTORY, input_img_path, IMG_HEIGHT, TEX_DIRECTORY, output_img_path, caption)
    
def generate_tex(stats_dir_path, reports_dir_path, probe_ext, output_ext):
    report = open(reports_dir_path + "/report.txt", "w+")
    
    filenames = sorted(os.listdir(stats_dir_path))
    
    for filename in filenames:
        if (filename.endswith(probe_ext) or filename.endswith(output_ext)) == False:
            continue
        else:
            name, ext = filename.split(".")
            img_type, probe_name, n , scans, detectors, opening = name.split("-")
            
            if img_type == "output":
                input_img_path = ('-').join(("input", probe_name, n, scans, detectors, opening))
                input_img_path = ('.').join((input_img_path, probe_ext))
                output_img_path = ('-').join(("output", probe_name, n, scans, detectors, opening))
                output_img_path = ('.').join((output_img_path, output_ext))
                
                partial_stats_path = ('-').join(("partial", probe_name, n, scans, detectors, opening))
                partial_stats_path = ('.').join((partial_stats_path, "txt"))
                
                partial_stats = open(stats_dir_path + "/" + partial_stats_path)
                RMSE = None
                
                for line in partial_stats:
                    attribute, value = line.split(" ")
                    
                    if attribute == "RMSE:":
                        RMSE = value
                        RMSE = round(float(RMSE), 2)
                        break
                
                partial_stats.close()
                    
                caption = "Scans: %s, Detectors: %s, Opening width: %s, RMSE: %s" % (scans, detectors, opening, RMSE)
                
                report.write(generate_tex_part(input_img_path, output_img_path, caption))
                report.write("\n")
    
    report.close()
    
if __name__ == "__main__":
    probe_name = "CT_ScoutView_large"
    probe_ext = "jpg"
    output_ext = "png"

    reports_dir_path = "reports/" + probe_name
    stats_dir_path = "stats/" + probe_name

    try:
        os.mkdir("reports")
    except:
        pass

    try:
        os.mkdir(reports_dir_path)
    except:
        pass
    
    generate_tex(stats_dir_path, reports_dir_path, probe_ext, output_ext)
    
    
    
    
