import os
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FantacalcioScraper(headless=True):
    def __init__(self):
        self.driver = None
        self.wait = None
        self.options = self._configure_railway_chrome_options()
    
    def _configure_railway_chrome_options(self):
        """Configura Chrome per Railway (ambiente containerizzato)"""
        options = Options()
        
        # ESSENZIALI per Railway/Docker
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Configurazioni per container
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Ottimizzazioni memoria per Railway
        options.add_argument('--memory-pressure-off')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-sync')
        
        # Gestione schermo virtuale
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # User agent realistico
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return options
    
    def start_driver(self):
        """Versione semplificata per Railway con Chromium"""
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            # Su Railway con Chromium, il driver è già nel PATH
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
            return True
            
        except Exception as e:
            logger.error(f"Errore driver: {e}")
            return False
    
    def _fallback_driver_setup(self):
        """Metodi di fallback per Railway"""
        try:
            # Fallback 1: Usa ChromeDriver di sistema
            logger.info("Tentativo fallback: ChromeDriver di sistema")
            
            # Cerca ChromeDriver nel PATH
            chrome_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/opt/chromedriver',
                'chromedriver'
            ]
            
            for path in chrome_paths:
                try:
                    service = Service(path)
                    self.driver = webdriver.Chrome(service=service, options=self.options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.wait = WebDriverWait(self.driver, 20)
                    logger.info(f"Driver di sistema avviato: {path}")
                    return True
                except:
                    continue
            
            # Fallback 2: ChromeDriver senza Service
            logger.info("Tentativo fallback: Senza Service")
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("Driver avviato senza Service")
            return True
            
        except Exception as e:
            logger.error(f"Tutti i fallback falliti: {e}")
            return False
    
    def quit_driver(self):
        """Chiude il driver in modo sicuro"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Driver chiuso correttamente")
        except Exception as e:
            logger.error(f"Errore chiusura driver: {e}")
    
    def login_angular_app(self, url, username, password):
        """
        Login specifico per applicazioni Angular con Ant Design
        """
        try:
            logger.info(f"Navigando verso: {url}")
            self.driver.get(url)
            
            # Attendi che Angular si carichi completamente
            time.sleep(5)  # Tempo più lungo per server cloud

            # Accetta i cookie se il banner è presente
            try:
                accept_cookies = self.driver.find_element(By.CSS_SELECTOR, "button[id='pt-accept-all']")
                if accept_cookies.is_displayed():
                    accept_cookies.click()
                    logger.info("Cookie accettati")
                    time.sleep(2)
            except NoSuchElementException:
                pass
            
            # Attendi che il form sia completamente renderizzato
            username_element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='username']"))
            )
            
            username_element.click()
            time.sleep(0.5)
            username_element.clear()
            username_element.send_keys(username)
            logger.info("Username inserito")
            
            time.sleep(1)
            
            password_element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='password']"))
            )
            password_element.click()
            time.sleep(0.5)
            password_element.clear()
            password_element.send_keys(password)
            logger.info("Password inserita")
            
            time.sleep(2)
            
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ant-btn-primary.ant-btn-block"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", login_button)
            logger.info("Bottone login cliccato")
            
            # Attesa più lunga per server cloud
            time.sleep(8)
            
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                logger.info("Login completato con successo!")
                return True
            else:
                logger.error("Login fallito - ancora nella pagina di login")
                return False
            
        except TimeoutException:
            logger.error("Timeout durante il login - elementi non trovati")
            return False
        except Exception as e:
            logger.error(f"Errore durante il login: {e}")
            return False
    
    def navigate_to_target_page(self, target_url):
        """Naviga alla pagina target dopo il login"""
        try:
            logger.info(f"Navigando alla pagina target: {target_url}")
            self.driver.get(target_url)
            time.sleep(5)  # Tempo extra per Angular su server cloud
            return True
        except Exception as e:
            logger.error(f"Errore nella navigazione: {e}")
            return False
    
    def find_formation(self, html_content):
        """
        Analizza l'HTML e restituisce lo stato delle formazioni
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        teams_with_formation = []
        teams_without_formation = []

        media_bodies = soup.find_all('div', class_='media-body')

        for media_body in media_bodies:
            h4_tag = media_body.find('h4', class_='media-heading ellipsis')
            h5_tag = media_body.find('h5')
            
            if h4_tag and h5_tag:
                team_name = h4_tag.get_text(strip=True)
                formation = h5_tag.get_text(strip=True)
                
                if team_name == 'GHOST':
                    continue
                
                if not formation:
                    teams_without_formation.append(team_name)
                else:
                    teams_with_formation.append((team_name, formation))

        return teams_with_formation, teams_without_formation
    
    def get_formations_status(self):
        """
        Esegue tutto il processo e restituisce lo stato delle formazioni
        """
        LOGIN_URL = "https://leghe.fantacalcio.it/login"
        TARGET_URL = "https://leghe.fantacalcio.it/feudoleague/formazioni"
        
        # Usa variabili d'ambiente per sicurezza
        USERNAME = os.getenv('FANTACALCIO_USERNAME')
        PASSWORD = os.getenv('FANTACALCIO_PASSWORD')
        
        try:
            if not self.start_driver():
                return None, "Errore nell'avvio del browser"
            
            if self.login_angular_app(LOGIN_URL, USERNAME, PASSWORD):
                if self.navigate_to_target_page(TARGET_URL):
                    time.sleep(5)
                    
                    html_content = self.driver.page_source
                    teams_with_formation, teams_without_formation = self.find_formation(html_content)
                    
                    return {
                        'with_formation': teams_with_formation,
                        'without_formation': teams_without_formation
                    }, None
                else:
                    return None, "Errore nella navigazione alla pagina delle formazioni"
            else:
                return None, "Errore nel login"
                
        except Exception as e:
            logger.error(f"Errore nel processo: {e}")
            return None, f"Errore generale: {str(e)}"
        finally:
            self.close()
    
    def close(self):
        """Chiude il browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class FantacalcioBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Aggiungi i handler
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("check", self.check_formations))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_message = (
            "🏈 **Benvenuto nel Bot Fantacalcio!** 🏈\n\n"
            "📋 Uso /check per controllare lo stato delle formazioni\n"
            "❓ Uso /help per vedere tutti i comandi disponibili\n\n"
            "⚡ Il bot controlla automaticamente chi ha inserito la formazione!"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_message = (
            "📋 **Comandi disponibili:**\n\n"
            "🚀 `/start` - Messaggio di benvenuto\n"
            "🔍 `/check` - Controlla lo stato delle formazioni\n"
            "❓ `/help` - Mostra questo messaggio\n\n"
            "⏱ **Nota:** Il controllo può richiedere 1-2 minuti"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def check_formations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /check per controllare le formazioni"""
        
        # Invia messaggio di attesa
        waiting_message = await update.message.reply_text(
            "🔄 Sto controllando le formazioni...\n"
            "⏳ Questo potrebbe richiedere 1-2 minuti\n"
            "☕ Nel frattempo prenditi un caffè!"
        )
        
        try:
            # Esegui lo scraping in un executor per non bloccare il bot
            loop = asyncio.get_event_loop()
            scraper = FantacalcioScraper(headless=True)
            
            result, error = await loop.run_in_executor(None, scraper.get_formations_status)
            
            if error:
                await waiting_message.edit_text(f"❌ **Errore:** {error}", parse_mode='Markdown')
                return
            
            if not result:
                await waiting_message.edit_text("❌ **Errore:** Nessun dato ricevuto", parse_mode='Markdown')
                return
            
            # Formatta il messaggio di risposta
            response_message = "🏈 **La situazione delle squadre è:**\n\n"
            
            # Tutte le squadre in un'unica lista ordinata
            all_teams = []
            
            # Aggiungi squadre con formazione
            for team_name, formation in result['with_formation']:
                all_teams.append((team_name, True, formation))
            
            # Aggiungi squadre senza formazione
            for team_name in result['without_formation']:
                all_teams.append((team_name, False, None))
            
            # Ordina alfabeticamente
            all_teams.sort(key=lambda x: x[0])
            
            # Formatta la lista
            for team_name, has_formation, formation in all_teams:
                if has_formation:
                    response_message += f"✅ **{team_name}** _{formation}_\n"
                else:
                    response_message += f"❌ **{team_name}**\n"
            
            # Riepilogo
            total_teams = len(all_teams)
            teams_ok = len(result['with_formation'])
            teams_missing = len(result['without_formation'])
            
            response_message += f"\n📊 **Riepilogo:**\n"
            response_message += f"🏆 Totale squadre: `{total_teams}`\n"
            response_message += f"✅ Con formazione: `{teams_ok}`\n"
            response_message += f"❌ Senza formazione: `{teams_missing}`\n"
            
            if teams_missing == 0:
                response_message += "\n🎉 **Tutte le squadre hanno inserito la formazione!**"
            else:
                response_message += f"\n⚠️ **{teams_missing} squadre devono ancora inserire la formazione**"
            
            # Aggiorna il messaggio (Telegram ha limite di 4096 caratteri)
            if len(response_message) > 4000:
                # Dividi in più messaggi se troppo lungo
                await waiting_message.edit_text("✅ **Controllo completato!**", parse_mode='Markdown')
                await update.message.reply_text(response_message, parse_mode='Markdown')
            else:
                await waiting_message.edit_text(response_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Errore nel comando check: {e}")
            await waiting_message.edit_text(
                f"❌ **Errore durante il controllo:**\n`{str(e)}`\n\n"
                "🔄 Riprova tra qualche minuto", 
                parse_mode='Markdown'
            )
    
    def run(self):
        """Avvia il bot"""
        logger.info("🤖 Avvio del bot Fantacalcio...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Ignora messaggi in coda
        )

def main():
    """Funzione principale con gestione sicura del token"""
    
    # Prova a ottenere il token dalle variabili d'ambiente
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print("🚀 Avvio del bot con token configurato...")
    
    # Crea e avvia il bot
    bot = FantacalcioBot(BOT_TOKEN)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot fermato dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore del bot: {e}")

if __name__ == "__main__":
    main()