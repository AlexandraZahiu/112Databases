-- =====================================================================
--  Dispecerat 112 – schema bazei de date + date demo
--  Compatibil: MySQL 8+ / MariaDB 10.4+
--
--  Import:  mysql -u root -p < database/schema.sql
-- =====================================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `dispecerat_112`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `dispecerat_112`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `Inter_pers`, `Raport_Interventii`, `Echipamente`,
                     `Personal_Interventie`, `Unitati_Interventie`,
                     `Locatii_Incidente`, `Interventii`, `Apelanti`,
                     `Apeluri`, `login`;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
--  Tabele
-- ---------------------------------------------------------------------

-- Apelurile primite la 112
CREATE TABLE `Apeluri` (
  `id_apel`       INT AUTO_INCREMENT PRIMARY KEY,
  `numar_apelant` VARCHAR(20),
  `ora_apel`      DATETIME,
  `tip_incident`  VARCHAR(255),
  `status_apel`   VARCHAR(50),               -- Deschis / În Progres / Închis
  UNIQUE KEY `uk_apeluri_numar` (`numar_apelant`)
) ENGINE=InnoDB;

-- Persoanele care au sunat
CREATE TABLE `Apelanti` (
  `id_apelant`    INT AUTO_INCREMENT PRIMARY KEY,
  `nume`          VARCHAR(100),
  `prenume`       VARCHAR(100),
  `adresa`        VARCHAR(255),
  `numar_apelant` VARCHAR(20),
  KEY `idx_apelanti_numar` (`numar_apelant`),
  CONSTRAINT `fk_apelanti_apeluri`
    FOREIGN KEY (`numar_apelant`) REFERENCES `Apeluri` (`numar_apelant`)
) ENGINE=InnoDB;

-- Intervențiile trimise în urma unui apel
CREATE TABLE `Interventii` (
  `id_interventie`     INT AUTO_INCREMENT PRIMARY KEY,
  `id_apel`            INT,
  `ora_start`          DATETIME,
  `ora_final`          DATETIME,
  `tip_interventie`    VARCHAR(100),         -- Ambulanță / Pompieri / Poliție / Salvamont
  `status_interventie` VARCHAR(50),          -- Planificată / În Progres / În Desfășurare / Finalizată
  KEY `idx_interventii_apel` (`id_apel`),
  CONSTRAINT `fk_interventii_apeluri`
    FOREIGN KEY (`id_apel`) REFERENCES `Apeluri` (`id_apel`)
) ENGINE=InnoDB;

-- Locația fiecărui incident
CREATE TABLE `Locatii_Incidente` (
  `id_locatie` INT AUTO_INCREMENT PRIMARY KEY,
  `adresa`     VARCHAR(255),
  `coordonate` VARCHAR(50),
  `id_apel`    INT,
  KEY `idx_locatii_apel` (`id_apel`),
  CONSTRAINT `fk_locatii_apeluri`
    FOREIGN KEY (`id_apel`) REFERENCES `Apeluri` (`id_apel`)
) ENGINE=InnoDB;

-- Unitățile de intervenție (ambulanță, pompieri, poliție...)
CREATE TABLE `Unitati_Interventie` (
  `id_unitate`     INT AUTO_INCREMENT PRIMARY KEY,
  `nume_unitate`   VARCHAR(100),
  `tip_unitate`    VARCHAR(50),
  `id_interventie` INT,
  KEY `idx_unitati_interventie` (`id_interventie`),
  CONSTRAINT `fk_unitati_interventii`
    FOREIGN KEY (`id_interventie`) REFERENCES `Interventii` (`id_interventie`)
) ENGINE=InnoDB;

-- Personalul de intervenție
CREATE TABLE `Personal_Interventie` (
  `id_personal` INT AUTO_INCREMENT PRIMARY KEY,
  `nume`        VARCHAR(100),
  `prenume`     VARCHAR(100),
  `functie`     VARCHAR(50),
  `id_unitate`  INT,
  KEY `idx_personal_unitate` (`id_unitate`),
  CONSTRAINT `fk_personal_unitati`
    FOREIGN KEY (`id_unitate`) REFERENCES `Unitati_Interventie` (`id_unitate`)
) ENGINE=InnoDB;

-- Tabelă de legătură many-to-many: Personal <-> Intervenții
CREATE TABLE `Inter_pers` (
  `id_inter_pers`  INT AUTO_INCREMENT PRIMARY KEY,
  `id_personal`    INT,
  `id_interventie` INT,
  KEY `idx_interpers_personal` (`id_personal`),
  KEY `idx_interpers_interventie` (`id_interventie`),
  CONSTRAINT `fk_interpers_personal`
    FOREIGN KEY (`id_personal`) REFERENCES `Personal_Interventie` (`id_personal`),
  CONSTRAINT `fk_interpers_interventii`
    FOREIGN KEY (`id_interventie`) REFERENCES `Interventii` (`id_interventie`)
) ENGINE=InnoDB;

-- Echipamentele folosite într-o intervenție
CREATE TABLE `Echipamente` (
  `id_echipament`  INT AUTO_INCREMENT PRIMARY KEY,
  `denumire`       VARCHAR(100),
  `tip_echipament` VARCHAR(50),
  `id_interventie` INT,
  KEY `idx_echipamente_interventie` (`id_interventie`),
  CONSTRAINT `fk_echipamente_interventii`
    FOREIGN KEY (`id_interventie`) REFERENCES `Interventii` (`id_interventie`)
) ENGINE=InnoDB;

-- Rapoartele scrise după fiecare intervenție
CREATE TABLE `Raport_Interventii` (
  `id_raport`      INT AUTO_INCREMENT PRIMARY KEY,
  `id_interventie` INT,
  `descriere`      TEXT,
  `recomandari`    TEXT,
  KEY `idx_raport_interventie` (`id_interventie`),
  CONSTRAINT `fk_raport_interventii`
    FOREIGN KEY (`id_interventie`) REFERENCES `Interventii` (`id_interventie`)
) ENGINE=InnoDB;

-- Conturile operatorilor (autentificare în aplicație)
CREATE TABLE `login` (
  `id`       INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `parola`   VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Date demo
-- ---------------------------------------------------------------------
--  Datele calendaristice sunt relative la momentul importului (NOW() - INTERVAL),
--  astfel încât statisticile „ultima lună / ultimul an” să aibă mereu date.
-- ---------------------------------------------------------------------

INSERT INTO `Apeluri` (`id_apel`, `numar_apelant`, `ora_apel`, `tip_incident`, `status_apel`) VALUES
(1,  '0722334455', NOW() - INTERVAL '74 13:30' DAY_MINUTE, 'Accident rutier',          'Deschis'),
(2,  '0741234567', NOW() - INTERVAL '14 11:30' DAY_MINUTE, 'Accident rutier',          'Deschis'),
(3,  '0759876543', NOW() - INTERVAL '67 11:00' DAY_MINUTE, 'Incendiu într-o clădire',  'În Progres'),
(4,  '0741122334', NOW() - INTERVAL '67 10:45' DAY_MINUTE, 'Leșin',                    'Închis'),
(5,  '0731000001', NOW() - INTERVAL '62 08:50' DAY_MINUTE, 'Explozie',                 'Deschis'),
(6,  '0732000002', NOW() - INTERVAL '61 11:45' DAY_MINUTE, 'Accident industrial',      'În Progres'),
(7,  '0733000003', NOW() - INTERVAL '61 04:00' DAY_MINUTE, 'Scurgere de gaze',         'Închis'),
(8,  '0734000004', NOW() - INTERVAL '60 13:30' DAY_MINUTE, 'Persoană dispărută',       'Deschis'),
(9,  '0735000005', NOW() - INTERVAL '60 10:00' DAY_MINUTE, 'Tâlhărie',                 'Închis'),
(10, '0747654321', NOW() - INTERVAL '67 10:00' DAY_MINUTE, 'Avarie gaz',               'În Progres'),
(11, '0751234567', NOW() - INTERVAL '67 09:30' DAY_MINUTE, 'Persoană blocată în lift', 'Deschis'),
(12, '0765432198', NOW() - INTERVAL '67 09:00' DAY_MINUTE, 'Incident rutier minor',    'Închis'),
(13, '0766411233', NOW() - INTERVAL '1227 09:47' DAY_MINUTE, 'Accident',                 'Închis'),
(14, '0722443556', NOW() - INTERVAL '42 01:39' DAY_MINUTE, 'Accident',                 'Deschis'),
(15, '0766413889', NOW() - INTERVAL '13 12:34' DAY_MINUTE, 'Accident',                 'În Progres'),
(16, '0766660021', NOW() - INTERVAL '13 12:21' DAY_MINUTE, 'Accident',                 'În Progres'),
(19, '0722345678', NOW() - INTERVAL '5 12:58' DAY_MINUTE, 'Incendiu',                 'Deschis'),
(20, '0789573569', NOW() - INTERVAL '5 12:42' DAY_MINUTE, 'Accident',                 'În Progres');

INSERT INTO `Apelanti` (`id_apelant`, `nume`, `prenume`, `adresa`, `numar_apelant`) VALUES
(1,  'Popescu',        'Ion',      'Str. Principala, nr. 10, București', '0722334455'),
(2,  'Popescu',        'Andrei',   'Strada Libertății 5',                '0741234567'),
(3,  'Ionescu',        'Maria',    'Strada Unirii 10',                   '0759876543'),
(4,  'Vasile',         'Ioana',    'Strada Călărași 2',                  '0741122334'),
(5,  'Matei',          'Adrian',   'Str. Mihai Bravu, Nr. 14, Galați',   '0731000001'),
(6,  'Constantinescu', 'Elena',    'Str. Teiului, Nr. 8, Ploiești',      '0732000002'),
(7,  'Cojocaru',       'Liviu',    'Str. Bradului, Nr. 22, Sibiu',       '0733000003'),
(8,  'Sandu',          'Carmen',   'Str. Trandafirului, Nr. 18, Oradea', '0734000004'),
(9,  'Ilie',           'George',   'Str. Fagului, Nr. 6, Iași',          '0735000005'),
(10, 'Dumitru',        'Alina',    'Strada Mihai Viteazul 12',           '0747654321'),
(11, 'Marinescu',      'George',   'Strada Horia 45',                    '0751234567'),
(12, 'Radu',           'Cristina', 'Strada Decebal 23',                  '0765432198'),
(13, 'Ionescu',        'Andrei',   'Str. Iuliu Maniu 112',               '0766660021'),
(16, 'Ion',            'Maria',    'Bd. Lujerului 75',                   '0722345678'),
(17, 'Popescu',        'Petrică',  'Munții Carpați',                     '0789573569');

INSERT INTO `Interventii` (`id_interventie`, `id_apel`, `ora_start`, `ora_final`, `tip_interventie`, `status_interventie`) VALUES
(1,  1,  NOW() - INTERVAL '74 13:25' DAY_MINUTE, NOW() - INTERVAL '74 12:50' DAY_MINUTE, 'Ambulanță', 'Finalizată'),
(2,  1,  NOW() - INTERVAL '67 11:20' DAY_MINUTE, NOW() - INTERVAL '67 11:00' DAY_MINUTE, 'Ambulanță', 'Finalizată'),
(3,  2,  NOW() - INTERVAL '67 10:50' DAY_MINUTE, NOW() - INTERVAL '67 10:00' DAY_MINUTE, 'Pompieri',  'În Desfășurare'),
(4,  3,  NOW() - INTERVAL '67 10:40' DAY_MINUTE, NOW() - INTERVAL '67 10:10' DAY_MINUTE, 'Ambulanță', 'Finalizată'),
(5,  4,  NOW() - INTERVAL '67 09:50' DAY_MINUTE, NOW() - INTERVAL '67 09:00' DAY_MINUTE, 'Pompieri',  'În Desfășurare'),
(6,  5,  NOW() - INTERVAL '67 09:20' DAY_MINUTE, NOW() - INTERVAL '67 08:50' DAY_MINUTE, 'Poliție',   'Finalizată'),
(7,  6,  NOW() - INTERVAL '67 08:45' DAY_MINUTE, NOW() - INTERVAL '67 08:00' DAY_MINUTE, 'Ambulanță', 'Finalizată'),
(18, 16, NOW() - INTERVAL '13 12:21' DAY_MINUTE, NOW() - INTERVAL '13 10:10' DAY_MINUTE, 'Poliție',   'Finalizată'),
(21, 19, NOW() - INTERVAL '5 12:58' DAY_MINUTE, NOW() - INTERVAL '5 11:10' DAY_MINUTE, 'Pompieri',  'Finalizată'),
(22, 20, NOW() - INTERVAL '5 12:42' DAY_MINUTE, NOW() - INTERVAL '5 08:10' DAY_MINUTE, 'Salvamont', 'Finalizată');

INSERT INTO `Locatii_Incidente` (`id_locatie`, `adresa`, `coordonate`, `id_apel`) VALUES
(1, 'Str. Principala, nr. 10, București', '44.4268, 26.1025', 1),
(2, 'Strada Libertății 5',                '44.4268, 26.1025', 1),
(3, 'Strada Unirii 10',                   '44.4268, 26.1025', 2),
(4, 'Strada Călărași 2',                  '44.4268, 26.1025', 3);

INSERT INTO `Unitati_Interventie` (`id_unitate`, `nume_unitate`, `tip_unitate`, `id_interventie`) VALUES
(1, 'Ambulanță București', 'Ambulanță', 1),
(2, 'Ambulanță București', 'Ambulanță', 1),
(3, 'Pompieri Sector 3',   'Pompieri',  2),
(4, 'Ambulanță Cluj',      'Ambulanță', 3),
(5, 'Poliție Sector 1',    'Poliție',   5),
(6, 'Ambulanță Ilfov',     'Ambulanță', 6);

INSERT INTO `Personal_Interventie` (`id_personal`, `nume`, `prenume`, `functie`, `id_unitate`) VALUES
(1, 'Ionescu',   'Mihai',  'Medic',            1),
(2, 'Georgescu', 'Mihai',  'Medic',            1),
(3, 'Popa',      'Ion',    'Pompier',          2),
(4, 'Ionescu',   'Elena',  'Șofer',            3),
(5, 'Ivan',      'Daniel', 'Agent Poliție',    5),
(6, 'Ciobanu',   'Raluca', 'Asistent Medical', 6);

INSERT INTO `Inter_pers` (`id_inter_pers`, `id_personal`, `id_interventie`) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 2, 2),
(4, 3, 3);

INSERT INTO `Echipamente` (`id_echipament`, `denumire`, `tip_echipament`, `id_interventie`) VALUES
(1, 'Defibrilator',       'medical', 1),
(2, 'Defibrilator',       'medical', 1),
(3, 'Mașină de pompieri', 'vehicul', 2),
(4, 'Ambulanță',          'vehicul', 3);

INSERT INTO `Raport_Interventii` (`id_raport`, `id_interventie`, `descriere`, `recomandari`) VALUES
(1,  1,  'Intervenția a fost finalizată fără incidente majore.', 'Monitorizare suplimentară a pacientului timp de 24 de ore.'),
(2,  1,  'Intervenție pentru accident rutier cu victime, pacientul a fost stabilizat și transportat la spital.', 'Monitorizare atentă la spital, eventual tratament post-traumatic.'),
(3,  2,  'Intervenție pentru incendiu într-o clădire. Pompierii au evacuat persoanele și au stins focul.', 'Verificări ulterioare pentru siguranța clădirii.'),
(4,  3,  'Leșin raportat. Pacienta a fost evaluată și transportată la spital pentru investigații suplimentare.', 'Investigații medicale pentru stabilirea cauzei leșinului.'),
(5,  5,  'Persoană blocată în lift evacuată de poliție și pompieri, fără victime.', 'Verificarea liftului și sistemului de întreținere.'),
(6,  6,  'Pacient transportat la spital după un accident rutier minor.', 'Recomandare pentru verificări medicale suplimentare.'),
(11, 22, 'Persoană leșinată pe traseu montan.', 'Snowmobil pentru evacuarea pacientului.');

-- Cont demo pentru autentificare
INSERT INTO `login` (`username`, `parola`) VALUES
('demo', 'demo123');
