"""
Dispecerat 112 – aplicație desktop pentru evidența apelurilor de urgență
și a intervențiilor (ambulanță, pompieri, poliție, salvamont).

Structura fișierului:
  1. Conexiune la baza de date
  2. Autentificare / creare cont
  3. Vizualizare tabele (CRUD: update status, ștergere, adăugare personal)
  4. Statistici (interogări complexe + grafic matplotlib)
  5. Formulare de adăugare (apel, echipament, raport intervenție)

Rulare:  python src/app.py   (vezi README.md pentru configurare)
"""

import logging
import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import Text, Toplevel, messagebox, ttk

import matplotlib.pyplot as plt
import mysql.connector
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mysql.connector import Error

try:
    # Opțional: citește variabilele din fișierul .env, dacă există
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Datele de conectare se citesc din variabile de mediu (fișierul .env),
# ca să nu fie scrise direct în cod.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "dispecerat_112"),
}


# Functie pentru a obtine conexiunea la baza de date
def obtine_conexiune():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        messagebox.showerror("Eroare", f"Eroare la conexiune: {str(e)}")
        return None

# Funcție pentru a crea un cont nou
def creare_cont():
    utilizator = entry_user.get()
    parola = entry_pass.get()
    
    # Verificăm dacă câmpurile nu sunt goale
    if utilizator == "" or parola == "":
        messagebox.showwarning("Avertizare", "Te rugăm să completezi toate câmpurile!")
        return

    # Conectare la baza de date și verificarea dacă utilizatorul există deja
    conn = obtine_conexiune()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE username = %s", (utilizator,))
            user_exist = cursor.fetchone()

            if user_exist:
                messagebox.showerror("Eroare", "Utilizatorul există deja. Alege un alt nume de utilizator.")
            else:
                # Inseram un nou utilizator în tabel
                cursor.execute("INSERT INTO login (username, parola) VALUES (%s, %s)", (utilizator, parola))
                conn.commit()
                messagebox.showinfo("Succes", "Contul a fost creat cu succes!")
                
                # După creare, poți să redirecționezi utilizatorul la login
                fereastra_login.destroy()
                deschide_login()

        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la crearea contului: {str(e)}")
        finally:
            conn.close()

# Funcție pentru a obține numele tuturor tabelelor (excluzând tabelul 'login')
def obtine_tabele():
    conn = obtine_conexiune()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tabele = cursor.fetchall()
            tabele_toate = [tabela[0] for tabela in tabele if tabela[0] != 'Inter_pers' and tabela[0] != 'login']  # Filtru pentru a exclude 'inter_pers' și 'login'
            return tabele_toate
        
        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la obținerea tabelelor: {str(e)}")
            return []
        finally:
            conn.close()
    return []



def vizualizeaza_tabel(tabel):
    conn = obtine_conexiune()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE {tabel}")
            descriere_tabel = cursor.fetchall()

            coloane = [col[0] for col in descriere_tabel if col[0].lower() != "id"]
            
            query = f"SELECT {', '.join(coloane)} FROM {tabel}"
            cursor.execute(query)
            rows = cursor.fetchall()

            fereastra_tabel = tk.Toplevel()
            fereastra_tabel.title(f"Vizualizare Tabel: {tabel}")
            center_window(fereastra_tabel, 1200, 500)  # Dimensiune ajustată
            
            culoare_fundal = "#B6C4CA"
            fereastra_tabel.config(bg=culoare_fundal)

            # Header Frame (peste partea de sus a paginii)
            header_frame = tk.Frame(fereastra_tabel, bg=culoare_fundal)
            header_frame.pack(fill=tk.X, pady=5)

            # Buton de Înapoi la Pagina Principală
            btn_back = ttk.Button(header_frame, text="Înapoi la Pagina Principală", command=lambda: fereastra_tabel.destroy())
            btn_back.pack(side=tk.LEFT, padx=5)
            
            # Adăugare buton `update_status_apel` doar în cazul tabelului Apeluri
            if tabel == "Apeluri":
                # Butoane de Actualizare Status și Ștergere Apel
                def update_status():
                    selected_item = treeview.selection()
                    if not selected_item:
                        messagebox.showwarning("Atenție", "Te rog selectează un apel din tabel!")
                        return

                    values = treeview.item(selected_item[0], 'values')
                    id_apel = values[0]  # Sau id-ul real pe care-l folosești

                    def confirma_actualizare():
                        new_status = combo_status.get()
                        if new_status:
                            try:
                                # Conexiune la baza de date
                                conn = obtine_conexiune()
                                cursor = conn.cursor()

                                # Executăm actualizarea statusului apelului în tabela Apeluri
                                cursor.execute(
                                    "UPDATE Apeluri SET status_apel = %s WHERE id_apel = %s",
                                    (new_status, id_apel)
                                )
                                if cursor.rowcount == 0:
                                    raise Exception(f"Nu a fost găsit apelul cu ID-ul {id_apel}.")
                                conn.commit()
                                messagebox.showinfo("Succes", f"Statusul apelului cu ID {id_apel} a fost actualizat la '{new_status}'!")
                                fereastra_update.destroy()
                            except Exception as e:
                                conn.rollback()
                                messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
                            finally:
                                conn.close()

                    # Fereastră pentru actualizare status
                    fereastra_update = tk.Toplevel()
                    fereastra_update.title("Actualizare Status")
                    fereastra_update.geometry("300x200")

                    tk.Label(fereastra_update, text="Selectează noul status:").pack(pady=10)

                    combo_status = ttk.Combobox(fereastra_update, values=["Deschis", "În Progres", "Închis"])
                    combo_status.pack(pady=10)

                    ttk.Button(fereastra_update, text="Confirmă", command=confirma_actualizare).pack(pady=10)

                btn_update_status = ttk.Button(header_frame, text="Actualizare Status Apel", command=update_status)
                btn_update_status.pack(side=tk.LEFT, padx=5)
    
            if tabel == "Apeluri":
                # Butoane de Ștergere Apel
                def sterge_apel(treeview):
                    selected_item = treeview.selection()
                    if not selected_item:
                        messagebox.showwarning("Atenție", "Te rog selectează un apel din tabel înainte de a șterge!")
                        return

                    # Obține datele și încearcă să convertească `id_apel` in int
                    values = treeview.item(selected_item[0], 'values')
                    try:
                        id_apel = int(values[0])  # id_apel este întotdeauna un număr valid
                    except (ValueError, TypeError) as e:
                        messagebox.showerror("Eroare", "ID-ul apelului selectat nu este valid.")
                        return

                    if not messagebox.askyesno("Confirmare", f"Sigur dorești să ștergi apelul cu ID {id_apel}?"):
                        return

                    try:
                        conn = obtine_conexiune()  
                        cursor = conn.cursor()  # obținem cursorul pentru executarea interogărilor

                    
                        conn.start_transaction()  

                        # Ștergere în cascadă, în ordinea copil -> părinte, într-o singură
                        # tranzacție: dacă un pas eșuează, se face rollback la tot.
                        # (Un singur DELETE multi-tabel cu JOIN eșuează pe InnoDB din cauza
                        #  cheilor străine, deoarece ordinea ștergerii nu este garantată.)
                        interventii_apel = "SELECT id_interventie FROM Interventii WHERE id_apel = %s"
                        pasi_stergere = [
                            f"DELETE FROM Echipamente WHERE id_interventie IN ({interventii_apel})",
                            f"DELETE FROM Raport_Interventii WHERE id_interventie IN ({interventii_apel})",
                            f"DELETE FROM Inter_pers WHERE id_interventie IN ({interventii_apel})",
                            # unitățile rămân în sistem, doar se eliberează de intervenție
                            f"UPDATE Unitati_Interventie SET id_interventie = NULL WHERE id_interventie IN ({interventii_apel})",
                            "DELETE FROM Interventii WHERE id_apel = %s",
                            "DELETE FROM Locatii_Incidente WHERE id_apel = %s",
                            "DELETE FROM Apelanti WHERE numar_apelant = (SELECT numar_apelant FROM Apeluri WHERE id_apel = %s)",
                            "DELETE FROM Apeluri WHERE id_apel = %s",
                        ]
                        for pas in pasi_stergere:
                            cursor.execute(pas, (id_apel,))

                        conn.commit()


                        messagebox.showinfo("Succes", f"Apelul cu ID {id_apel} și toate datele asociate au fost șterse cu succes!")
                        treeview.delete(selected_item[0])  
                    except mysql.connector.Error as e:
                        logging.error(f"Eroare la ștergere: {str(e)}")
                        messagebox.showerror("Eroare", f"A apărut o problemă la ștergerea apelului. Detalii: {str(e)}")
                        conn.rollback()  
                    except Exception as e:
                        logging.error(f"Eroare la ștergere: {str(e)}")
                        conn.rollback()  
                        messagebox.showerror("Eroare", f"A apărut o problemă la ștergerea apelului. Detalii: {str(e)}")
                    finally:
                        conn.close()

                btn_stergere = ttk.Button(header_frame, text="Șterge Apel", command=lambda: sterge_apel(treeview))
                btn_stergere.pack(side=tk.LEFT, padx=5)
            if tabel == "Interventii":
    # Buton de Actualizare Status Intervenție
                def update_status_interventie():
                    selected_item = treeview.selection()
                    if not selected_item:
                        messagebox.showwarning("Atenție", "Te rog selectează o intervenție din tabel!")
                        return

                    values = treeview.item(selected_item[0], 'values')
                    id_interventie = values[0]  

                    def confirma_actualizare_interventie():
                        new_status = combo_status.get()
                        if new_status:
                            try:
                                conn = obtine_conexiune()
                                cursor = conn.cursor()

                                # Interogare complexă cu main SELECT  pentru update status interventie
                                query = """
                                    UPDATE Interventii
                                    SET status_interventie = %s,
                                        ora_final = (
                                            SELECT CASE 
                                                WHEN %s = 'Finalizată' THEN (
                                                    SELECT NOW() -- Prima subcerere pentru ora curentă
                                                )
                                                ELSE ora_final
                                            END
                                        )
                                    WHERE id_interventie = (
                                        SELECT id_interventie FROM (
                                            SELECT id_interventie FROM Interventii WHERE id_interventie = %s -- A doua subcerere pentru validare
                                        ) AS subquery
                                    );
                                """

                                cursor.execute(query, (new_status, new_status, id_interventie))

                                if cursor.rowcount == 0:
                                    raise Exception(f"Nu a fost găsită intervenția cu ID-ul {id_interventie}.")

                                conn.commit()
                                messagebox.showinfo("Succes", f"Statusul intervenției cu ID {id_interventie} a fost actualizat la '{new_status}'!")
                                fereastra_update.destroy()
                            except Exception as e:
                                conn.rollback()
                                messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
                            finally:
                                conn.close()

                    # Fereastră pentru actualizare status
                    fereastra_update = tk.Toplevel()
                    fereastra_update.title("Actualizare Status Intervenție")
                    fereastra_update.geometry("300x200")

                    tk.Label(fereastra_update, text="Selectează noul status:").pack(pady=10)

                    combo_status = ttk.Combobox(fereastra_update, values=["Planificată", "În Progres", "Finalizată"])
                    combo_status.pack(pady=10)

                    ttk.Button(fereastra_update, text="Confirmă", command=confirma_actualizare_interventie).pack(pady=10)

                btn_update_status_interventie = ttk.Button(header_frame, text="Actualizare Status Intervenție", command=update_status_interventie)
                btn_update_status_interventie.pack(side=tk.LEFT, padx=5)

            if tabel == "Personal_Interventie":
                # Buton pentru stergere Personal
                def sterge_personal(treeview):
                    selected_item = treeview.selection()
                    if not selected_item:
                        messagebox.showwarning("Atenție", "Te rog selectează o persoană din tabel înainte de a șterge!")
                        return

                    values = treeview.item(selected_item[0], 'values')
                    id_personal = values[0] 

                    if not messagebox.askyesno("Confirmare", f"Sigur dorești să ștergi persoana cu ID {id_personal}?"):
                        return

                    try:
                        conn = obtine_conexiune()
                        cursor = conn.cursor()
                        # Mai întâi ștergem asocierile cu intervențiile (tabela de legătură),
                        # apoi persoana, altfel cheia străină din Inter_pers blochează ștergerea
                        cursor.execute("DELETE FROM Inter_pers WHERE id_personal = %s", (id_personal,))
                        cursor.execute("DELETE FROM Personal_Interventie WHERE id_personal = %s", (id_personal,))
                        if cursor.rowcount == 0:
                            raise Exception("Nu s-a găsit personalul pentru ștergere.")
                        conn.commit()
                        messagebox.showinfo("Succes", f"Persoana cu ID {id_personal} a fost ștearsă cu succes!")
                        treeview.delete(selected_item[0])  
                    except Exception as e:
                        conn.rollback()
                        messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
                    finally:
                        conn.close()

                btn_sterge_personal = ttk.Button(header_frame, text="Șterge Personal", command=lambda: sterge_personal(treeview))
                btn_sterge_personal.pack(side=tk.LEFT, padx=5)

                # Buton pentru Adăugare Personal
                def adauga_personal():
                    def confirma_adaugare():
                        nume = entry_nume.get()
                        prenume = entry_prenume.get()
                        functie = entry_functie.get()
                        id_unitate = entry_id_unitate.get()

                        if not nume or not prenume or not functie or not id_unitate:
                            messagebox.showwarning("Atenție", "Toate câmpurile sunt obligatorii!")
                            return

                        try:
                            id_unitate = int(id_unitate)  # verifica daca este numeric
                            conn = obtine_conexiune()
                            cursor = conn.cursor()

                            # Verifică dacă id_unitate există
                            cursor.execute("SELECT COUNT(*) FROM Unitati_Interventie WHERE id_unitate = %s", (id_unitate,))
                            if cursor.fetchone()[0] == 0:
                                messagebox.showerror("Eroare", f"ID-ul unității {id_unitate} nu există în tabela Unitati_Interventie.")
                                return

                            # Inserare personal nou în tabela Personal_Interventie
                            cursor.execute(
                                "INSERT INTO Personal_Interventie (nume, prenume, functie, id_unitate) VALUES (%s, %s, %s, %s)",
                                (nume, prenume, functie, id_unitate)
                            )
                            conn.commit()
                            messagebox.showinfo("Succes", f"Persoana {nume} {prenume} a fost adăugată cu succes!")
                            fereastra_adaugare.destroy()
                            reload_all_data()  # Reîncarcă toate datele
                        except Exception as e:
                            conn.rollback()
                            messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
                        finally:
                            conn.close()


                    # Fereastră pentru adăugare personal
                    fereastra_adaugare = tk.Toplevel()
                    fereastra_adaugare.title("Adaugă Personal")
                    fereastra_adaugare.geometry("400x350")

                    tk.Label(fereastra_adaugare, text="Nume:").pack(pady=5)
                    entry_nume = tk.Entry(fereastra_adaugare)
                    entry_nume.pack(pady=5)

                    tk.Label(fereastra_adaugare, text="Prenume:").pack(pady=5)
                    entry_prenume = tk.Entry(fereastra_adaugare)
                    entry_prenume.pack(pady=5)

                    tk.Label(fereastra_adaugare, text="Funcție:").pack(pady=5)
                    entry_functie = tk.Entry(fereastra_adaugare)
                    entry_functie.pack(pady=5)

                    tk.Label(fereastra_adaugare, text="ID Unitate:").pack(pady=5)
                    entry_id_unitate = tk.Entry(fereastra_adaugare)
                    entry_id_unitate.pack(pady=5)

                    ttk.Button(fereastra_adaugare, text="Confirmă", command=confirma_adaugare).pack(pady=10)

                btn_adauga_personal = ttk.Button(header_frame, text="Adaugă Personal", command=adauga_personal)
                btn_adauga_personal.pack(side=tk.LEFT, padx=5)
            if tabel == "Echipamente":
                # Buton de Ștergere Echipament
                def sterge_echipament(treeview):
                    selected_item = treeview.selection()
                    if not selected_item:
                        messagebox.showwarning("Atenție", "Te rog selectează un echipament din tabel înainte de a șterge!")
                        return

                    # Obține datele și încearcă să convertească `id_echipament` la int
                    values = treeview.item(selected_item[0], 'values')
                    try:
                        id_echipament = int(values[0])  
                    except (ValueError, TypeError) as e:
                        messagebox.showerror("Eroare", "ID-ul echipamentului selectat nu este valid.")
                        return

                    if not messagebox.askyesno("Confirmare", f"Sigur dorești să ștergi echipamentul cu ID {id_echipament}?"):
                        return

                    try:
                        conn = obtine_conexiune()  
                        cursor = conn.cursor() 

                        conn.start_transaction() 

                        # Interogare pentru a șterge toate legăturile legate de echipament
                        cursor.execute("""
                            DELETE e
                                FROM Echipamente e
                                JOIN Interventii i ON i.id_interventie = e.id_interventie
                                JOIN Apeluri a ON i.id_apel = a.id_apel
                                WHERE e.id_echipament = %s

                        """, (id_echipament,))

                        conn.commit()

                        messagebox.showinfo("Succes", f"Echipamentul cu ID {id_echipament} și toate datele asociate au fost șterse cu succes!")
                        treeview.delete(selected_item[0])  
                    except mysql.connector.Error as e:
                        logging.error(f"Eroare la ștergere: {str(e)}")
                        messagebox.showerror("Eroare", f"A apărut o problemă la ștergerea echipamentului. Detalii: {str(e)}")
                        conn.rollback()
                    except Exception as e:
                        logging.error(f"Eroare la ștergere: {str(e)}")
                        conn.rollback()
                        messagebox.showerror("Eroare", f"A apărut o problemă la ștergerea echipamentului. Detalii: {str(e)}")
                    finally:
                        conn.close()

                btn_stergere_echipament = ttk.Button(header_frame, text="Șterge Echipament", command=lambda: sterge_echipament(treeview))
                btn_stergere_echipament.pack(side=tk.LEFT, padx=5)
            treeview_frame = tk.Frame(fereastra_tabel, bg=culoare_fundal)
            treeview_frame.pack(expand=True, fill=tk.BOTH)

            treeview = ttk.Treeview(treeview_frame, columns=coloane, show="headings", selectmode="browse")
            
            for col in coloane:
                treeview.heading(col, text=col)
                treeview.column(col, width=150, anchor="center") 

            scrollbar_vertical = ttk.Scrollbar(treeview_frame, orient="vertical", command=treeview.yview)
            treeview.config(yscrollcommand=scrollbar_vertical.set)
            scrollbar_vertical.pack(side="right", fill="y")

            scrollbar_horizontal = ttk.Scrollbar(treeview_frame, orient="horizontal", command=treeview.xview)
            treeview.config(xscrollcommand=scrollbar_horizontal.set)
            scrollbar_horizontal.pack(side="bottom", fill="x")

            treeview.pack(expand=True, fill=tk.BOTH)

            # bara de căutare și butonul de căutare
            footer_frame = tk.Frame(fereastra_tabel, bg=culoare_fundal)
            footer_frame.pack(fill=tk.X, pady=10)

            search_label = tk.Label(footer_frame, text="Căutare:")
            search_label.pack(side=tk.LEFT, padx=5)

            search_entry = tk.Entry(footer_frame, font=("Segoe UI", 12), width=30)
            search_entry.pack(side=tk.LEFT, padx=5)

            def cauta_in_tabel():
                termen_cautare = search_entry.get().lower()  
                filtered_rows = [row for row in rows if any(termen_cautare in str(value).lower() for value in row)]
                
                for row in treeview.get_children():
                    treeview.delete(row)
                for row in filtered_rows:
                    treeview.insert("", tk.END, values=row)

            search_button = ttk.Button(footer_frame, text="Căutare", command=cauta_in_tabel)
            search_button.pack(side=tk.LEFT, padx=5)

            def reload_all_data():
                for row in treeview.get_children():
                    treeview.delete(row)
                for row in rows:
                    treeview.insert("", tk.END, values=row)

            reload_button = ttk.Button(footer_frame, text="Reîncarcă Toate Datele", command=reload_all_data)
            reload_button.pack(side=tk.RIGHT, padx=5)

            for row in rows:
                treeview.insert("", tk.END, values=row)

        except Error as e:
            logging.error(f"Eroare la obținerea datelor din tabel: {str(e)}")
            messagebox.showerror("Eroare", f"Eroare la obținerea datelor din tabel: {str(e)}")
        finally:
            conn.close()

def create_table_window(tabel, rows, columns):
    fereastra_tabel = tk.Toplevel()
    fereastra_tabel.title(f"Vizualizare Tabel: {tabel}")
    center_window(fereastra_tabel, 1000, 500)  
    culoare_fundal = "#546745"
    fereastra_tabel.config(bg=culoare_fundal)
    
    treeview_frame = tk.Frame(fereastra_tabel, bg=culoare_fundal)
    treeview_frame.pack(expand=True, fill=tk.BOTH)
    

    if columns:
        treeview = ttk.Treeview(treeview_frame, columns=columns, show="headings")
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=150, anchor="center")

        for row in rows:
            treeview.insert("", tk.END, values=row)
    else:
        print(f"Tabelul '{tabel}' nu este recunoscut.")
    
    treeview.pack(expand=True, fill=tk.BOTH)
    
 
    return treeview


def deschide_login():
    global fereastra_login
    fereastra_login = tk.Tk()
    fereastra_login.title("Autentificare")
    fereastra_login.config(bg="#DDD7D7") 
    center_window(fereastra_login, 400, 300) 

    label_user = tk.Label(fereastra_login, text="Utilizator", bg="#DDD7D7", font=("Helvetica Neue ", 14))
    label_user.pack(pady=10)
    global entry_user
    entry_user = tk.Entry(fereastra_login, font=("Segoe UI", 12), width=30)  
    entry_user.pack(pady=5)

    label_pass = tk.Label(fereastra_login, text="Parolă", bg="#DDD7D7", font=("Segoe UI", 14))
    label_pass.pack(pady=10)
    global entry_pass
    entry_pass = tk.Entry(fereastra_login, show="*",font=("Segoe UI", 12), width=30)  
    entry_pass.pack(pady=5)


    btn_login = ttk.Button(fereastra_login, text="Autentificare", command=autentificare)
    btn_login.pack(pady=20)

    btn_creare_cont = ttk.Button(fereastra_login, text="Crează un cont", command=creare_cont)
    btn_creare_cont.pack(pady=10)
    fereastra_login.mainloop()

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    position_top = int(screen_height / 2 - height / 2)
    position_right = int(screen_width / 2 - width / 2)
    window.geometry(f'{width}x{height}+{position_right}+{position_top}')

# Funcție de autentificare
def autentificare():
    utilizator = entry_user.get()
    parola = entry_pass.get()

    if utilizator == "" or parola == "":
        messagebox.showwarning("Avertizare", "Te rugăm să completezi toate câmpurile!")
        return

    conn = obtine_conexiune()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE username = %s AND parola = %s", (utilizator, parola))
            user_exist = cursor.fetchone()

            if user_exist:
                messagebox.showinfo("Succes", "Autentificare reușită!")
                deschide_meniu_principal()
            else:
                messagebox.showerror("Eroare", "Date de autentificare incorecte!")

        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la autentificare: {str(e)}")
        finally:
            conn.close()

def deschide_meniu_principal():
    fereastra_meniu = tk.Toplevel()
    fereastra_meniu.title("Meniu Principal")
    center_window(fereastra_meniu, 650, 400)
    culoare_fundal = "#546745"
    fereastra_meniu.config(bg=culoare_fundal)

    btn_tabele = ttk.Button(fereastra_meniu, text="Afișează toate tabelele", command=afiseaza_tabele)
    btn_tabele.pack(pady=30)

    btn_statistici = ttk.Button(fereastra_meniu, text="Statistici Apeluri", command=statistici)
    btn_statistici.pack(pady=15)
    
    btn_statistici = ttk.Button(fereastra_meniu, text="Statistici Personal", command=statistici_personal)
    btn_statistici.pack(pady=15)
    btn_apel_nou = ttk.Button(fereastra_meniu, text="Adaugă Apel", command=adauga_apel)
    btn_apel_nou.pack(pady=15)
    

    btn_adauga_echipament = ttk.Button(fereastra_meniu, text="Adaugă Echipament", command=adauga_echipament)
    btn_adauga_echipament.pack(pady=10)

    buton_adauga_raport = ttk.Button(fereastra_meniu, text="Adaugă raport intervenție", command=deschide_formular_raport_interventie)
    buton_adauga_raport.pack(pady=10)



# Funcție pentru a afișa lista cu tabele
def afiseaza_tabele():
    tabele = obtine_tabele()

    fereastra_tabele = tk.Toplevel()
    fereastra_tabele.title("Lista Tabele")
    center_window(fereastra_tabele, 600, 600)
    culoare_fundal = "#546745"
    fereastra_tabele.config(bg=culoare_fundal)
    for tabel in tabele:
        btn_tabel = ttk.Button(fereastra_tabele, text=tabel, command=lambda t=tabel: vizualizeaza_tabel(t))
        btn_tabel.pack(pady=15)

    fereastra_tabele.mainloop()
    
   
def statistici():
    conn = obtine_conexiune()
    if conn:
        try:
            cursor = conn.cursor()

            # Configurare fereastră statistici
            fereastra_statistici = tk.Toplevel()
            fereastra_statistici.title("Statistici")
            center_window(fereastra_statistici, 580, 800)
            culoare_fundal = "#546745"
            fereastra_statistici.config(bg=culoare_fundal)

            # Creare cadru scrollabil
            container = tk.Frame(fereastra_statistici)
            container.pack(fill="both", expand=True)

            canvas = tk.Canvas(container, bg=culoare_fundal)
            scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=culoare_fundal)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Date pentru interogări
            data_curenta = datetime.now()
            prima_zi_luna_trecuta = data_curenta - timedelta(days=30)
            data_inceput_an = data_curenta - timedelta(days=365)

            # Apeluri din ultima lună și ultimul an
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) 
                        FROM Apeluri 
                        WHERE ora_apel BETWEEN %s AND %s) AS apeluri_luna_trecuta,
                        (SELECT COUNT(*) 
                            FROM Apeluri 
                            WHERE ora_apel BETWEEN %s AND %s) AS apeluri_an_trecut
            """, (prima_zi_luna_trecuta, data_curenta, data_inceput_an, data_curenta))
            result = cursor.fetchone()
            apeluri_luna_trecuta = result[0]
            apeluri_an_trecut = result[1]

            # Interogare pentru pie chart: Tipuri de intervenții
            cursor.execute("""
                SELECT i.tip_interventie, COUNT(*) 
                FROM Interventii i
                WHERE i.status_interventie = 'Finalizată'
                GROUP BY i.tip_interventie
            """)
            rezultate_interventii = cursor.fetchall()

            # Pregătire date pentru pie chart
            tipuri_interventii = [r[0] for r in rezultate_interventii]
            numar_interventii = [r[1] for r in rezultate_interventii]

            # Adăugare pie chart
            fig, ax = plt.subplots(figsize=(5.6, 5.6))
            ax.pie(
                numar_interventii,
                labels=tipuri_interventii,
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.Paired(range(len(numar_interventii)))
            )
            ax.axis('equal')

            piechart_canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
            piechart_canvas.get_tk_widget().pack(pady=10)
            piechart_canvas.draw()

            # Afișare date apeluri
            label_apeluri = tk.Label(
                scrollable_frame, 
                text=f"Apeluri luna trecută: {apeluri_luna_trecuta}\nApeluri ultimul an: {apeluri_an_trecut}", 
                bg=culoare_fundal, 
                fg="white"
            )
            label_apeluri.pack(pady=10)

            # Interogare pentru durata medie a intervențiilor pe unitate și tip
            cursor.execute("""
    SELECT 
        u.nume_unitate, 
        i.tip_interventie, 
        CONCAT(p.nume, ' ', p.prenume) AS personal_implicat,
        AVG(TIMESTAMPDIFF(MINUTE, i.ora_start, i.ora_final)) AS durata_medie
    FROM Unitati_Interventie u
    JOIN Interventii i ON u.id_interventie = i.id_interventie
    JOIN Inter_pers ip ON i.id_interventie = ip.id_interventie
    JOIN Personal_Interventie p ON ip.id_personal = p.id_personal
    WHERE i.ora_final IS NOT NULL
    GROUP BY u.nume_unitate, i.tip_interventie, personal_implicat
    ORDER BY durata_medie ASC;
""")
            durata_medie_interventii = cursor.fetchall()

# Afișare durata medie
            label_durata = tk.Label(
                scrollable_frame, 
                text="Durata medie a intervențiilor pe unitate, tip și personal implicat:", 
                bg=culoare_fundal, 
                fg="white"
            )
            label_durata.pack(pady=10)

            for unitate, tip, personal_implicat, durata in durata_medie_interventii:
                durata_label = tk.Label(
                    scrollable_frame, 
                    text=f"Unitate: {unitate}, Tip: {tip}, Personal implicat: {personal_implicat}, Durata medie: {durata:.2f} minute", 
                    bg=culoare_fundal, 
                    fg="white"
                )
                durata_label.pack()

            # Interogare pentru top 5 apelanți
            cursor.execute("""
                SELECT 
                    ap.nume, 
                    ap.prenume, 
                    COUNT(a.id_apel) AS numar_apeluri,
                    GROUP_CONCAT(DISTINCT li.adresa SEPARATOR '; ') AS locatii
                FROM Apelanti ap
                JOIN Apeluri a ON ap.numar_apelant = a.numar_apelant
                LEFT JOIN Locatii_Incidente li ON a.id_apel = li.id_apel
                WHERE a.ora_apel >= %s
                GROUP BY ap.id_apelant
                ORDER BY numar_apeluri DESC
                LIMIT 5;

            """, (data_inceput_an,))
            top_apelanti = cursor.fetchall()

            # Afișare top 5 apelanți
            label_top_apelanti = tk.Label(
                scrollable_frame, 
                text="Top 5 apelanți cu cele mai multe apeluri în ultimul an:", 
                bg=culoare_fundal, 
                fg="white"
            )
            label_top_apelanti.pack(pady=10)

            for nume, prenume, numar_apeluri, locatii in top_apelanti:
                apelant_label = tk.Label(
                    scrollable_frame, 
                    text=f"{nume} {prenume}: {numar_apeluri} apeluri. Locații incidente: {locatii}", 
                    bg=culoare_fundal, 
                    fg="white",
                    wraplength=500  # Textul va fi împărțit pe mai multe linii dacă este prea lung
                )
                apelant_label.pack()

            # Interogare pentru top 5 locații cu cele mai multe incidente raportate
           
            query = """
                SELECT 
                    li.adresa, 
                    COUNT(li.id_apel) AS numar_incidente,
                    (SELECT COUNT(*) 
                    FROM Apeluri a 
                    WHERE a.id_apel = li.id_apel AND a.ora_apel >= %s) AS apeluri_recente,
                    (SELECT GROUP_CONCAT(DISTINCT i.tip_interventie SEPARATOR '; ') 
                    FROM Interventii i 
                    WHERE i.id_apel = li.id_apel) AS tipuri_interventii
                FROM 
                    Locatii_Incidente li
                GROUP BY 
                    li.adresa
                ORDER BY 
                    numar_incidente DESC
                LIMIT 5;
            """
            cursor.execute(query, (data_inceput_an,))
            locatii_incidente = cursor.fetchall()


            # Afișare top 5 locații cu cele mai multe incidente
         
            label_locatii = tk.Label(
                scrollable_frame,
                text="Top 5 locații cu cele mai multe incidente raportate:",
                bg=culoare_fundal,
                fg="white",
                font=("Arial", 12, "bold")
            )
            label_locatii.pack(pady=10)

            for adresa, numar_incidente, apeluri_recente, tipuri_interventii in locatii_incidente:
                locatii_label = tk.Label(
                    scrollable_frame,
                    text=f"Adresa: {adresa}, Număr incidente: {numar_incidente}, Apeluri recente: {apeluri_recente}, Tipuri intervenții: {tipuri_interventii}",
                    bg=culoare_fundal,
                    fg="white",
                    wraplength=500
                )
                locatii_label.pack()



        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la obținerea statisticilor: {str(e)}")
        finally:
            conn.close()

def ore_lucrate_unitate():
    conn = obtine_conexiune()
    ore_lucrate_lista = []  # Listă pentru a stoca rezultatele

    if conn:
        try:
            cursor = conn.cursor()  # Creăm cursor doar dacă conexiunea este deschisă

            cursor.execute("""
                SELECT 
                    u.tip_unitate, 
                    u.nume_unitate, 
                    COUNT(DISTINCT u.id_unitate) AS numar_unitati,
                    SUM(TIMESTAMPDIFF(HOUR, i.ora_start, i.ora_final)) AS total_ore
                FROM 
                    Interventii i
                INNER JOIN 
                    Unitati_Interventie u ON i.id_interventie = u.id_interventie
                INNER JOIN 
                    Personal_Interventie pi ON u.id_unitate = pi.id_unitate
                WHERE 
                    i.ora_final IS NOT NULL  -- Verifica doar intervențiile finalizate
                GROUP BY 
                    u.tip_unitate, u.nume_unitate
                ORDER BY 
                    total_ore DESC;
            """)
            
            unitati_ore = cursor.fetchall()  # Recuperăm rezultatele

            if unitati_ore:
                for tip, nume_unitate, nr_unitati, total_ore in unitati_ore:
                    # Adăugăm rezultatele într-o listă
                    ore_lucrate_lista.append({
                        "tip_unitate": tip,
                        "nume_unitate": nume_unitate,
                        "numar_unitati": nr_unitati,
                        "total_ore": total_ore
                    })
            
            cursor.close()  # Închidem cursorul după folosire
            
        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la obținerea statisticilor: {str(e)}")
        
        finally:
            if conn and conn.is_connected():
                conn.close()  # Închidem conexiunea doar dacă este deschisă

    return ore_lucrate_lista


def statistici_personal():
    conn = obtine_conexiune()
    cursor = None
    if conn:
        try:
            if conn.is_connected():
                cursor = conn.cursor()  # Creăm cursor doar dacă conexiunea este deschisă
                
                # Configurare fereastră statistici
                fereastra_statistici = tk.Toplevel()
                fereastra_statistici.title("Statistici")
                center_window(fereastra_statistici, 450, 450)
                culoare_fundal = "#546745"
                fereastra_statistici.config(bg=culoare_fundal)

                # Canvas pentru scrollbar
                canvas = tk.Canvas(fereastra_statistici, bg=culoare_fundal)
                scrollbar = tk.Scrollbar(fereastra_statistici, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg=culoare_fundal)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="right", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                # Interogare 1: Unitățile implicate în cele mai multe intervenții
                cursor.execute("""
                    SELECT 
                        u.nume_unitate, 
                        u.tip_unitate, 
                        COUNT(iu.id_interventie) AS numar_interventii
                    FROM 
                        Unitati_Interventie u
                    INNER JOIN Interventii iu ON u.id_interventie = iu.id_interventie
                    INNER JOIN  Raport_Interventii r ON r.id_interventie=u.id_interventie
                    GROUP BY 
                        u.id_unitate, u.nume_unitate, u.tip_unitate
                    ORDER BY 
                        numar_interventii DESC;
                """)
                unitati_interventii = cursor.fetchall()

                # Interogare 2: Personalul cu cel mai mare număr de intervenții
                cursor.execute("""
                    SELECT 
                        p.nume, 
                        p.prenume, 
                        p.functie, 
                        COUNT(ip.id_interventie) AS numar_interventii
                    FROM 
                        Personal_Interventie p
                    INNER JOIN Inter_pers ip ON p.id_personal = ip.id_personal
                    GROUP BY 
                        p.id_personal, p.nume, p.prenume, p.functie
                    ORDER BY 
                        numar_interventii DESC
                    LIMIT 1;
                """)
                personal_top = cursor.fetchall()

                # Afișare unități cu cele mai multe intervenții
                label_unitati = tk.Label(
                    scrollable_frame, 
                    text="Unitățile cu cele mai multe intervenții:", 
                    bg=culoare_fundal, 
                    fg="white", 
                    font=("Arial", 12, "bold")
                )
                label_unitati.pack(pady=10)

                for unitate, tip, numar in unitati_interventii:
                    unitate_label = tk.Label(
                        scrollable_frame, 
                        text=f"Unitate: {unitate}, Tip: {tip}, Număr intervenții: {numar}", 
                        bg=culoare_fundal, 
                        fg="white"
                    )
                    unitate_label.pack()

                # Afișare personal cu cele mai multe intervenții
                label_personal = tk.Label(
                    scrollable_frame, 
                    text="Personalul cu cele mai multe intervenții:", 
                    bg=culoare_fundal, 
                    fg="white", 
                    font=("Arial", 12, "bold")
                )
                label_personal.pack(pady=10)

                for nume, prenume, functie, numar in personal_top:
                    personal_label = tk.Label(
                        scrollable_frame, 
                        text=f"{nume} {prenume}, Funcție: {functie}, Număr intervenții: {numar}", 
                        bg=culoare_fundal, 
                        fg="white"
                    )
                    personal_label.pack()

                # Adăugare Interogare Tipurile de echipamente utilizate cel mai frecvent
                cursor.execute("""
                    SELECT 
                        e.tip_echipament,
                        (SELECT COUNT(DISTINCT i.id_interventie)
                         FROM Interventii i
                         WHERE i.id_interventie = e.id_interventie) AS numar_interventii,
                        (SELECT COUNT(e1.id_echipament)
                         FROM Echipamente e1
                         WHERE e1.tip_echipament = e.tip_echipament) AS numar_total_echipamente
                    FROM Echipamente e
                    GROUP BY e.tip_echipament
                    ORDER BY numar_interventii DESC, numar_total_echipamente DESC;
                """)
                echipamente_stats = cursor.fetchall()

                # Afișare rezultate interogare 19
                label_echipamente = tk.Label(
                    scrollable_frame, 
                    text="Tipurile de echipamente utilizate frecvent:", 
                    bg=culoare_fundal, 
                    fg="white", 
                    font=("Arial", 12, "bold")
                )
                label_echipamente.pack(pady=10)

                for tip, numar_interventii, numar_total in echipamente_stats:
                    echipamente_label = tk.Label(
                        scrollable_frame, 
                        text=f"Tip: {tip}, Număr intervenții: {numar_interventii}, Total echipamente: {numar_total}", 
                        bg=culoare_fundal, 
                        fg="white"
                    )
                    echipamente_label.pack()

        except Error as e:
            messagebox.showerror("Eroare", f"Eroare la obținerea statisticilor: {str(e)}")
        finally:
            if cursor:
                cursor.close()  # Închidem cursorul dacă nu a fost deja închis
            if conn and conn.is_connected():
                conn.close()  # Închidem conexiunea doar dacă este deschisă

def adauga_apel():
    fereastra_apel = tk.Toplevel()
    fereastra_apel.title("Adaugă Apel")
    center_window(fereastra_apel, 500, 600)


    tk.Label(fereastra_apel, text="Număr Apelant:", font=("Segoe UI", 12)).pack(pady=5)
    entry_telefon = tk.Entry(fereastra_apel, font=("Segoe UI", 12))
    entry_telefon.pack(pady=5)

    tk.Label(fereastra_apel, text="Tip Incident:", font=("Segoe UI", 12)).pack(pady=5)
    combo_tip_incident = ttk.Combobox(fereastra_apel, font=("Segoe UI", 12), values=["Incendiu", "Accident", "Altele"])
    combo_tip_incident.pack(pady=5)

    tk.Label(fereastra_apel, text="Status Apel:", font=("Segoe UI", 12)).pack(pady=5)
    combo_status_apel = ttk.Combobox(fereastra_apel, font=("Segoe UI", 12), values=["Deschis", "În Progres", "Închis"])
    combo_status_apel.pack(pady=5)


    tk.Label(fereastra_apel, text="Nume Apelant:", font=("Segoe UI", 12)).pack(pady=5)
    entry_nume = tk.Entry(fereastra_apel, font=("Segoe UI", 12))
    entry_nume.pack(pady=5)

    tk.Label(fereastra_apel, text="Prenume Apelant:", font=("Segoe UI", 12)).pack(pady=5)
    entry_prenume = tk.Entry(fereastra_apel, font=("Segoe UI", 12))
    entry_prenume.pack(pady=5)

    tk.Label(fereastra_apel, text="Adresă Apelant:", font=("Segoe UI", 12)).pack(pady=5)
    entry_adresa = tk.Entry(fereastra_apel, font=("Segoe UI", 12))
    entry_adresa.pack(pady=5)


    tk.Label(fereastra_apel, text="Tip Intervenție:", font=("Segoe UI", 12)).pack(pady=5)
    combo_tip_interventie = ttk.Combobox(fereastra_apel, font=("Segoe UI", 12), values=["Ambulanță", "Pompieri", "Poliție", "Salvamont"])
    combo_tip_interventie.pack(pady=5)

    tk.Label(fereastra_apel, text="Status Intervenție:", font=("Segoe UI", 12)).pack(pady=5)
    combo_status_interventie = ttk.Combobox(fereastra_apel, font=("Segoe UI", 12), values=["În Desfășurare", "Finalizată"])
    combo_status_interventie.pack(pady=5)


    def salveaza_apel():
        numar_apelant = entry_telefon.get()
        tip_incident = combo_tip_incident.get()
        status_apel = combo_status_apel.get()
        nume = entry_nume.get()
        prenume = entry_prenume.get()
        adresa = entry_adresa.get()
        tip_interventie = combo_tip_interventie.get()
        status_interventie = combo_status_interventie.get()

        if not (numar_apelant and tip_incident and status_apel and nume and prenume and adresa and tip_interventie and status_interventie):
            messagebox.showwarning("Avertizare", "Completează toate câmpurile!")
            return

        conn = obtine_conexiune()
        if conn:
            try:
                cursor = conn.cursor()

                # Inserăm în tabelul Apeluri
                cursor.execute("""
                    INSERT INTO Apeluri (numar_apelant, tip_incident, status_apel, ora_apel)
                    VALUES (%s, %s, %s, NOW())
                """, (numar_apelant, tip_incident, status_apel))
                id_apel = cursor.lastrowid

                # Inserăm în tabelul Apelanti
                cursor.execute("""
                    INSERT INTO Apelanti (nume, prenume, adresa, numar_apelant)
                    VALUES (%s, %s, %s, %s)
                """, (nume, prenume, adresa, numar_apelant))

                # Inserăm în tabelul Interventii
                cursor.execute("""
                    INSERT INTO Interventii (id_apel, ora_start, tip_interventie, status_interventie)
                    VALUES (%s, NOW(), %s, %s)
                """, (id_apel, tip_interventie, status_interventie))

                conn.commit()
                messagebox.showinfo("Succes", "Apelul a fost adăugat cu succes!")
                fereastra_apel.destroy()

            except Error as e:
                messagebox.showerror("Eroare", f"Eroare la salvarea apelului: {str(e)}")
                conn.rollback()  
            finally:
                conn.close()

    tk.Button(fereastra_apel, text="Salvează Apel", command=salveaza_apel, font=("Segoe UI", 12)).pack(pady=20)
    
def adauga_raport_interventie(id_interventie, descriere, recomandari):
        conn = obtine_conexiune()
        if conn:
            try:
                cursor = conn.cursor()

                # Verificăm dacă id_interventie este valid
                cursor.execute("SELECT COUNT(*) FROM Interventii WHERE id_interventie = %s", (id_interventie,))
                rezultat = cursor.fetchone()
                if rezultat[0] == 0:
                    messagebox.showerror("Eroare", "ID-ul intervenției nu există în baza de date!")
                    return

                # Verificăm câmpurile descriere și recomandări
                if not descriere:
                    messagebox.showwarning("Avertizare", "Descrierea este necesară!")
                    return

                # Inserăm datele în tabelul Raport_Interventii
                cursor.execute(
                    "INSERT INTO Raport_Interventii (id_interventie, descriere, recomandari) "
                    "VALUES (%s, %s, %s)",
                    (id_interventie, descriere, recomandari)
                )
                conn.commit()  # Commit tranzacția
                messagebox.showinfo("Succes", "Raportul de intervenție a fost adăugat cu succes!")
            except Error as e:
                conn.rollback()  # Rollback în caz de eroare
                messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
            finally:
                conn.close()

def deschide_formular_raport_interventie():
    # Creăm o nouă fereastră
    fereastra_raport = Toplevel()
    fereastra_raport.title("Adaugă raport de intervenție")
    fereastra_raport.geometry("400x400")
    culoare_fundal = "#546745"
    fereastra_raport.config(bg=culoare_fundal)
    # Label și Combobox pentru ID intervenție
    tk.Label(fereastra_raport, text="ID intervenție:").pack(pady=5)
    combo_id_interventie = ttk.Combobox(fereastra_raport, font=("Segoe UI", 12), width=30)
    combo_id_interventie.pack(pady=5)

    # Obținem lista de ID-uri valide din tabela Interventii
    try:
        conn = obtine_conexiune()
        cursor = conn.cursor()
        cursor.execute("SELECT id_interventie FROM Interventii")
        iduri_interventii = [str(row[0]) for row in cursor.fetchall()]
        combo_id_interventie['values'] = iduri_interventii
    except Error as e:
        messagebox.showerror("Eroare", f"Nu am putut încărca intervențiile: {str(e)}")
    finally:
        conn.close()

    # Label și Textbox pentru descriere
    tk.Label(fereastra_raport, text="Descriere intervenție:").pack(pady=5)
    descriere_entry = Text(fereastra_raport, height=5, width=30)
    descriere_entry.pack(pady=5)

    # Label și Textbox pentru recomandări
    tk.Label(fereastra_raport, text="Recomandări:").pack(pady=5)
    recomandari_entry = Text(fereastra_raport, height=5, width=30)
    recomandari_entry.pack(pady=5)

    # Funcția pentru a adăuga raportul
    def adauga_raport():
        id_interventie = combo_id_interventie.get().strip()
        descriere = descriere_entry.get("1.0", "end-1c").strip()
        recomandari = recomandari_entry.get("1.0", "end-1c").strip()
        adauga_raport_interventie(id_interventie, descriere, recomandari)

    ttk.Button(fereastra_raport, text="Adaugă raport", command=adauga_raport).pack(pady=20)

def adauga_echipament():
    def confirma_adaugare():
        denumire = entry_denumire.get()
        tip_echipament = entry_tip_echipament.get()
        id_interventie = combo_id_interventie.get()

        if denumire == "" or tip_echipament == "" or id_interventie == "":
            messagebox.showwarning("Avertizare", "Te rugăm să completezi toate câmpurile!")
            return

        try:
            conn = obtine_conexiune()
            cursor = conn.cursor()

            # Verificăm dacă id_interventie este valid
            cursor.execute("SELECT COUNT(*) FROM Interventii WHERE id_interventie = %s", (id_interventie,))
            rezultat = cursor.fetchone()
            if rezultat[0] == 0:
                messagebox.showerror("Eroare", "ID Intervenție nu există!")
                return

            # Executăm inserarea noului echipament în tabela Echipamente
            cursor.execute(
                "INSERT INTO Echipamente (denumire, tip_echipament, id_interventie) VALUES (%s, %s, %s)",
                (denumire, tip_echipament, id_interventie)
            )
            conn.commit()
            messagebox.showinfo("Succes", "Echipamentul a fost adăugat cu succes!")

            # Închidem fereastra de adăugare echipament
            fereastra_adaugare.destroy()
        except Error as e:
            conn.rollback()
            messagebox.showerror("Eroare", f"A apărut o problemă: {str(e)}")
        finally:
            conn.close()

    # Fereastră pentru adăugare echipament
    fereastra_adaugare = tk.Toplevel()
    fereastra_adaugare.title("Adăugare Echipament")
    fereastra_adaugare.geometry("400x350")
    culoare_fundal = "#546745"
    fereastra_adaugare.config(bg=culoare_fundal)
    tk.Label(fereastra_adaugare, text="Denumire Echipament:").pack(pady=10)
    entry_denumire = tk.Entry(fereastra_adaugare, font=("Segoe UI", 12), width=30)
    entry_denumire.pack(pady=5)

    tk.Label(fereastra_adaugare, text="Tip Echipament:").pack(pady=10)
    entry_tip_echipament = tk.Entry(fereastra_adaugare, font=("Segoe UI", 12), width=30)
    entry_tip_echipament.pack(pady=5)

    tk.Label(fereastra_adaugare, text="ID Intervenție:").pack(pady=10)
    combo_id_interventie = ttk.Combobox(fereastra_adaugare, font=("Segoe UI", 12), width=28)
    combo_id_interventie.pack(pady=5)

    # Populăm combobox-ul cu valorile ID-urilor existente în tabela Interventii
    try:
        conn = obtine_conexiune()
        cursor = conn.cursor()
        cursor.execute("SELECT id_interventie FROM Interventii")
        iduri_interventii = [str(row[0]) for row in cursor.fetchall()]
        combo_id_interventie['values'] = iduri_interventii
    except Error as e:
        messagebox.showerror("Eroare", f"Nu am putut încărca intervențiile: {str(e)}")
    finally:
        conn.close()

    ttk.Button(fereastra_adaugare, text="Confirmă", command=confirma_adaugare).pack(pady=20)

# Punctul de pornire al aplicației
if __name__ == "__main__":
    deschide_login()
