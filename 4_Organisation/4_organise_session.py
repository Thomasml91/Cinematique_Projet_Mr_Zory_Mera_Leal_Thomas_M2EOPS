# ============================================================
#   4_organise_session.py   (VERSION STABLE - PDF SANS ERREUR)
# ============================================================




import os
import shutil
import csv
import json
import numpy as np
import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos








# ===================== PATHS =====================




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)




VIDEOS_DIR = os.path.join(ROOT_DIR, "1_Fichiers_Vidéos")
EXPORT_ROOT = os.path.join(ROOT_DIR, "5_exports")
INDEX_CSV = os.path.join(EXPORT_ROOT, "index_sessions.csv")




os.makedirs(EXPORT_ROOT, exist_ok=True)








# ===================== METADATA INPUT =====================




def ask_metadata():

    def clean_alpha(prompt):
        while True:
            val = input(prompt).strip()
            if val and val.replace(" ", "").replace("-", "").isalpha():
                return val
            print("❌ Lettres uniquement.")

    def clean_date():
        while True:
            val = input("Date du test (JJ/MM/AAAA) : ").strip()
            parts = val.split("/")
            if len(parts) == 3:
                j, m, a = parts
                if (len(j)==2 and len(m)==2 and len(a)==4
                        and j.isdigit() and m.isdigit() and a.isdigit()
                        and 1 <= int(j) <= 31
                        and 1 <= int(m) <= 12
                        and 2000 <= int(a) <= 2100):
                    return val
            print("❌ Format invalide.")

    def clean_digit(prompt):
        while True:
            val = input(prompt).strip()
            if val.isdigit() and int(val) > 0:
                return val
            print("❌ Nombre invalide.")

    def clean_essai():
        while True:
            val = input("Essai (1 ou 2) : ").strip()
            if val in ["1", "2"]:
                return val
            print("❌ Tape 1 ou 2.")

    def clean_periode():
        print("\nPeriode menstruelle ?")
        print("1 = REGLES")
        print("2 = HORS_REGLES")
        while True:
            val = input("Choix : ").strip()
            if val == "1": return "REGLES"
            if val == "2": return "HORS_REGLES"
            print("❌ Choix invalide.")

    # =========================
    # 🔥 SÉLECTION PERSONNE EXISTANTE (recherche par frappe)
    # =========================
    nom = None
    prenom = None

    if os.path.exists(INDEX_CSV):
        df_idx = pd.read_csv(INDEX_CSV)
        if "nom" in df_idx.columns and len(df_idx) > 0:

            personnes = df_idx[["nom", "prenom"]].drop_duplicates().reset_index(drop=True)

            print("\n==== RECHERCHE ATHLÈTE ====")
            print("Tape les premières lettres du nom ou prénom (ou tape 0 = nouvelle personne)")
            print("===========================")

            while True:
                query = input("Recherche : ").strip().lower()

                if query == "0":
                    break

                # Filtrage sur nom OU prénom
                mask = (
                        personnes["nom"].str.lower().str.startswith(query) |
                        personnes["prenom"].str.lower().str.startswith(query)
                )
                resultats = personnes[mask].reset_index(drop=True)

                if len(resultats) == 0:
                    print("  Aucun résultat. Réessaie ou tape 0 pour créer une nouvelle personne.")
                    continue

                # Affiche les correspondances numérotées
                print(f"\n  {len(resultats)} résultat(s) :")
                for i, row in resultats.iterrows():
                    print(f"  {i + 1} - {row['prenom']} {row['nom']}")
                print("  [Entrée] pour affiner | 0 pour nouvelle personne")

                choix = input("  Sélection : ").strip()

                if choix == "0":
                    break
                if choix == "":
                    continue  # affiner la recherche
                if choix.isdigit() and 1 <= int(choix) <= len(resultats):
                    row = resultats.iloc[int(choix) - 1]
                    nom = row["nom"]
                    prenom = row["prenom"]
                    print(f"✅ Sélectionné : {prenom} {nom}")
                    break
                print("❌ Choix invalide.")

    # Si nouvelle personne
    if nom is None:
        nom = clean_alpha("Nom : ")
        prenom = clean_alpha("Prenom : ")

    # =========================
    # SAISIE DES INFOS VARIABLES
    # =========================
    meta = {
        "nom": nom,
        "prenom": prenom,
        "date": clean_date(),
        "session": clean_digit("Numero de session : "),
        "essai": clean_essai(),
        "periode": clean_periode()
    }

    # =========================
    # BOUCLE DE MODIFICATION
    # =========================
    while True:
        print("\n========= VERIFICATION =========")
        print(f"1 - Nom : {meta['nom']}")
        print(f"2 - Prenom : {meta['prenom']}")
        print(f"3 - Date : {meta['date']}")
        print(f"4 - Session : {meta['session']}")
        print(f"5 - Essai : DJ{meta['essai']}")
        print(f"6 - Periode : {meta['periode']}")
        print("C - Confirmer")
        print("===============================")

        choice = input("Modifier quoi ? ").lower()

        if choice == "1": meta["nom"] = clean_alpha("Nom : ")
        elif choice == "2": meta["prenom"] = clean_alpha("Prenom : ")
        elif choice == "3": meta["date"] = clean_date()
        elif choice == "4": meta["session"] = clean_digit("Numero de session : ")
        elif choice == "5": meta["essai"] = clean_essai()
        elif choice == "6": meta["periode"] = clean_periode()
        elif choice == "c": break

    # BASE NAME
    base = f"{meta['nom'].replace(' ','_')}_{meta['prenom'].replace(' ','_')}_{meta['date'].replace('/','-')}_S{meta['session']}_DJ{meta['essai']}"

    # ANTI DOUBLON
    if os.path.exists(INDEX_CSV):
        df = pd.read_csv(INDEX_CSV)
        if "base_name" in df.columns and base in df["base_name"].values:
            print("\n⚠️ ATTENTION — cette session existe déjà !")
            while True:
                rep = input("Continuer quand même ? (O/N) : ").lower()
                if rep == "n":
                    print("\n🔁 Re-saisie complète.\n")
                    return ask_metadata()
                elif rep == "o":
                    break

    meta["base"] = base
    return meta








# ===================== FOLDERS =====================




def build_session_folder(meta):
   d = os.path.join(EXPORT_ROOT,f"{meta['nom']}_{meta['prenom']}",f"{meta['date'].replace('/','-')}_S{meta['session']}",f"DJ{meta['essai']}")
   os.makedirs(d,exist_ok=True)
   return d




def move(src,dst):
   if os.path.exists(src):
       shutil.move(src,dst)
       print("✔",src,"→",dst)








# ===================== PDF =====================




def title(pdf,meta):
   pdf.add_page()
   pdf.set_font("Helvetica","B",22)
   pdf.cell(0,12,"Analyse Drop Jump",align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
   pdf.ln(4)
   pdf.set_font("Helvetica","",13)
   pdf.cell(0,8,f"Athlete : {meta['prenom']} {meta['nom']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
   pdf.cell(0,8,f"Date : {meta['date']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
   pdf.cell(0,8,f"Session : {meta['session']}   Essai : DJ{meta['essai']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
   pdf.cell(0,8,f"Periode menstruelle : {meta['periode']}",new_x=XPos.LMARGIN,new_y=YPos.NEXT)




def img(pdf,title,path):
   if os.path.exists(path):
       pdf.add_page()
       pdf.set_font("Helvetica","B",14)
       pdf.cell(0,10,title,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
       pdf.image(path,x=15,w=180)








# ===================== PDF BUILDER =====================




def build_pdf(meta,folder):




   pdf=FPDF()
   pdf.set_auto_page_break(True,15)




   # TITLE
   title(pdf,meta)




   # ==================== IMAGES ====================
   B=meta["base"]




   img(pdf,"Frontale 0-100ms",f"{folder}/{B}_valgus_0_100ms.png")
   img(pdf,"Frontale 10Hz absolu",f"{folder}/{B}_valgus_angles_absolus_10Hz.png")
   img(pdf,"Frontale 10Hz valgus-varus",f"{folder}/{B}_valgus_varus_10Hz.png")
   img(pdf,"Frontale Global",f"{folder}/{B}_FRONTAL_GLOBAL.png")
   img(pdf,"Frontale Fenetre IC 100ms",f"{folder}/{B}_FRONTAL_WINDOW_100ms.png")




   img(pdf,"Sagittale Genou 0-100ms",f"{folder}/{B}_sagittal_knee_0_100ms.png")
   img(pdf,"Sagittale Tronc 0-100ms",f"{folder}/{B}_sagittal_trunk_0_100ms.png")
   img(pdf,"Sagittale Genou 10Hz",f"{folder}/{B}_sagittal_knee_10Hz.png")
   img(pdf,"Sagittale Tronc 10Hz",f"{folder}/{B}_sagittal_trunk_10Hz.png")
   img(pdf,"Sagittale Global",f"{folder}/{B}_SAGITTAL_GLOBAL.png")








   # ==================== EXTRACTION CSV UNIQUE ====================




   # FRONT
   F=f"{folder}/{B}_angles_valgus.csv"
   if os.path.exists(F):
       df=pd.read_csv(F).iloc[-1]
       pdf.add_page()
       pdf.set_font("Helvetica","B",15)
       pdf.cell(0,10,"Resume Frontal",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
       pdf.ln(3)
       pdf.set_font("Helvetica","",12)
       pdf.multi_cell(0,7,
f"""
Valgus IC Droit : {df.get('valgus_IC_R')}
Valgus IC Gauche : {df.get('valgus_IC_L')}
Peak 100ms Droit : {df.get('peak_100ms_R')}
Peak 100ms Gauche : {df.get('peak_100ms_L')}
Delta 100ms Droit : {df.get('delta_100ms_R')}
Delta 100ms Gauche : {df.get('delta_100ms_L')}
Peak Global Droit : {df.get('peak_global_R')}
Peak Global Gauche : {df.get('peak_global_L')}
""")




   # SAG
   S=f"{folder}/{B}_angles_sagittal.csv"
   if os.path.exists(S):
       df=pd.read_csv(S).iloc[-1]
       pdf.add_page()
       pdf.set_font("Helvetica","B",15)
       pdf.cell(0,10,"Resume Sagittal",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
       pdf.ln(3)
       pdf.set_font("Helvetica","",12)
       pdf.multi_cell(0,7,
f"""
Genou IC : {df.get('IC_knee')}
Tronc IC : {df.get('IC_trunk')}
Peak Genou 100ms : {df.get('peak_knee_100')}
Peak Tronc 100ms : {df.get('peak_trunk_100')}
Delta Genou 100ms : {df.get('delta_knee_100')}
Delta Tronc 100ms : {df.get('delta_trunk_100')}
Peak Genou Global : {df.get('peak_knee_global')}
Peak Tronc Global : {df.get('peak_trunk_global')}
""")




   pdf.output(f"{folder}/{B}_rapport.pdf")
   print("\nPDF GENERE ->",f"{folder}/{B}_rapport.pdf")




# ============================================================
#  EXTRACTION POUR INDEX CSV  (⚠ À placer hors de build_pdf)
# ============================================================




def extract_values_for_index(folder, base):




   vals = {}




   # FRONT CSV
   F = f"{folder}/{base}_angles_valgus.csv"
   if os.path.exists(F):
       df = pd.read_csv(F).iloc[-1]
       vals.update({
           "valgus_IC_R": df.get("valgus_IC_R"),
           "valgus_IC_L": df.get("valgus_IC_L"),
           "peak_100ms_R": df.get("peak_100ms_R"),
           "peak_100ms_L": df.get("peak_100ms_L"),
           "delta_100ms_R": df.get("delta_100ms_R"),
           "delta_100ms_L": df.get("delta_100ms_L"),
           "peak_global_R": df.get("peak_global_R"),
           "peak_global_L": df.get("peak_global_L"),
       })




   # SAG CSV
   S = f"{folder}/{base}_angles_sagittal.csv"
   if os.path.exists(S):
       df = pd.read_csv(S).iloc[-1]
       vals.update({
           "IC_knee": df.get("IC_knee"),
           "IC_trunk": df.get("IC_trunk"),
           "peak_knee_100": df.get("peak_knee_100"),
           "peak_trunk_100": df.get("peak_trunk_100"),
           "delta_knee_100": df.get("delta_knee_100"),
           "delta_trunk_100": df.get("delta_trunk_100"),
           "peak_knee_global": df.get("peak_knee_global"),
           "peak_trunk_global": df.get("peak_trunk_global"),
       })




   return vals














# ===================== MAIN =====================




def main():




   print("\n==== ARCHIVAGE DROP JUMP ====\n")




   meta=ask_metadata()
   folder=build_session_folder(meta)




   collect=[
       "angles_valgus.csv","angles_sagittal.csv",
       "valgus_0_100ms.png","valgus_abs_0_100ms.png","valgus_angles_absolus_10Hz.png",
       "valgus_varus_10Hz.png","FRONTAL_GLOBAL.png","FRONTAL_WINDOW_100ms.png",
       "sagittal_knee_0_100ms.png","sagittal_knee_10Hz.png","sagittal_trunk_0_100ms.png",
       "sagittal_trunk_10Hz.png","SAGITTAL_0_100ms.png","SAGITTAL_GLOBAL.png",
       "parametres_selection_frontale.json", "parametres_selection_sagittale.json",
       "valgus_pose_angles_annotated.mp4","sagittal_pose_angles_annotated.mp4", "frames_peak_frontal",
   ]




   for f in collect:
       move(f"{VIDEOS_DIR}/{f}",f"{folder}/{meta['base']}_{f}")
       # déplacement du dossier frames_peaks_frontale
       if os.path.isdir(f"{VIDEOS_DIR}/frames_peaks_frontale"):
           shutil.move(f"{VIDEOS_DIR}/frames_peaks_frontale", f"{folder}/{meta['base']}_frames_peaks_frontale")
           print("✔ frames_peaks_frontale  →  déplacé")


   build_pdf(meta,folder)


   # ---- ENREGISTREMENT INDEX GLOBAL ----
   vals = {
       "base_name": meta["base"],
       "nom": meta["nom"],
       "prenom": meta["prenom"],
       "date_session": meta["date"],
       "session_num": meta["session"],
       "essai_label": f"DJ{meta['essai']}",
       "periode_menstruelle": meta["periode"],
       "trial_dir": folder
   }


   # ajoute ensuite toutes les valeurs biomécaniques
   vals.update(extract_values_for_index(folder, meta["base"]))


   # Enregistrement dans index_sessions.csv
   if os.path.exists(INDEX_CSV):
       df = pd.read_csv(INDEX_CSV)
       df = pd.concat([df, pd.DataFrame([vals])], ignore_index=True)
   else:
       df = pd.DataFrame([vals])


   df.to_csv(INDEX_CSV, index=False)


   print("\n📁 Index mis à jour ->", INDEX_CSV)


   print("\n==== FIN OK ====\n")




if __name__=="__main__":
   main()











