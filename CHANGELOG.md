# Changelog

## 0.13.0

- Sjednoceno přihlášení do Inbox Assistantu a autorizace Gmail API do jednoho Google OAuth flow.
- Po přihlášení už aplikace při analýze inboxu, práci se štítky ani AI vyhledávání nespouští druhé Google přihlášení.
- Gmail API nyní používá access token z aktuálního přihlášeného Streamlit uživatele.
- Odstraněn původní lokální InstalledAppFlow.run_local_server() z běžného provozu aplikace.
- Přihlášení bylo ověřeno po odhlášení a novém přihlášení; analýza inboxu funguje bez dalšího OAuth dialogu.
- Zachována multi-user identita a existující uživatelská data včetně AI Search indexu.
- Odstraněna dočasná diagnostika access tokenu a testovacího volání Gmail API z app.py.

## 0.12.1

- Multi-user databázová architektura nyní používá oddělené `user_id`.
- Gmail OAuth tokeny jsou ukládány odděleně podle uživatele.
- AI vyhledávání nyní rozpoznává časové podmínky v dotazu.
- Dotazy jako „faktury za poslední dva měsíce“ používají tvrdý časový filtr nad Gmail `internalDate`.
- E-maily mimo požadované období se vůbec neposílají do AI rerankingu.
- Přidána podpora výrazů jako „poslední týden“, „poslední 3 měsíce“, „dnes“, „včera“, „minulý měsíc“ a „minulý rok“.
- Aktivní časový filtr je zobrazen nad výsledky.
- Opraveno přepínání řazení mezi Relevancí a Nejnovějšími.
- Přepnutí řazení nyní okamžitě přerovná již nalezené výsledky bez nového vyhledávání.

## 0.12.0

- Zahájena migrace Inbox Assistantu na multi-user architekturu.
- Přidán uživatelský kontext aplikace.
- SQLite databáze nyní odděluje data pomocí `user_id`.
- Původní data jsou při první migraci automaticky přiřazena profilu `local-dev`.
- Multi-user izolace byla přidána pro nastavení, historii koše, historii odhlášení, AI Search index, feedback, aliasy a klasifikační pravidla.
- Primární a unikátní klíče databáze byly upraveny tak, aby stejné Gmail message ID nebo odesílatel mohl existovat nezávisle u více uživatelů.
- Gmail OAuth token už není globální `token.json`.
- Tokeny jsou ukládány odděleně do `user_tokens/` podle uživatelského profilu.
- Starý `token.json` je při prvním použití bezpečně zkopírován do profilu `local-dev`; původní soubor se nemaže.
- Připraven základ pro budoucí přihlášení externích testerů.

## 0.11.4

- Přidán bezpečný fallback při selhání automatického one-click odhlášení.
- Při chybách HTTP 401, 403 nebo 405 může Inbox Assistant nabídnout ruční otevření odhlašovací stránky.
- HTML odhlašovací odkaz se nyní uchovává jako záložní možnost i v případě, že zpráva podporuje one-click unsubscribe.
- Po ručním odhlášení lze akci potvrdit a uložit do historie odhlášení.
- Přidána uživatelská pravidla klasifikace podle e-mailové adresy odesílatele.
- Newsletter nebo reklamu lze označit jako „Není newsletter/reklama“.
- Běžný e-mail lze označit jako „Vždy newsletter/reklama“.
- Uživatelské pravidlo má při další analýze přednost před AI klasifikací.
- Přidán přehled uložených klasifikačních pravidel s možností jejich odstranění.

## 0.11.3

- Přidáno datum a čas přijetí e-mailu do všech karet v Inbox analýze.
- Dnešní zprávy se zobrazují ve formátu „dnes v HH:MM“.
- Včerejší zprávy se zobrazují ve formátu „včera v HH:MM“.
- Starší zprávy zobrazují přesné datum a čas.
- U starších zpráv je doplněna orientační relativní informace, například „před 3 měsíci“.
- Datum přijetí je zobrazeno přímo pod odesílatelem.

## 0.11.2

- Opraveno spuštění AI vyhledávání klávesou Enter.
- Vyhledávání nyní používá callback přímo na poli Dotaz.
- Tlačítko Hledat zůstává jako alternativní způsob spuštění stejné akce.
- Backend se oproti verzi 0.11.1 nemění.

## 0.11.1

- Vyhledávání lze nově spustit klávesou Enter.
- Vyhledávací pole bylo přesunuto do formuláře Streamlit.
- Upraveno počáteční chování AI vyhledávání.
- U nových dotazů bez historie je AI méně přísná a vrací širší sadu potenciálně relevantních výsledků.
- Cílem prvního hledání je umožnit uživateli výsledky dále zpřesňovat pomocí Relevantní / Nerelevantní.
- Jakmile existuje feedback nebo známý pojem, vyhledávání začne více využívat personalizované signály.
- Známé osoby a aliasy zůstávají silným bonusem, ale nejsou podmínkou nalezení výsledků.
- Rozšířena první várka kandidátních e-mailů.
- Zachováno tlačítko Najít další pro pokračování v hledání.

## 0.11.0

- Přidána zpětná vazba k výsledkům AI vyhledávání.
- Výsledek lze označit jako Relevantní nebo Nerelevantní.
- Feedback se ukládá lokálně do inbox_assistant.db.
- Nerelevantní zprávy se při stejném hledání potlačí.
- Pozitivně hodnocení odesílatelé dostávají při dalším hledání vyšší prioritu.
- Přidána možnost naučit asistenta vlastní pojmy a osoby.
- Lze například uložit vazbu „majitelka bytu“ → konkrétní odesílatel.
- Naučené pojmy se při dalších dotazech používají jako silný vyhledávací signál.
- Vyhledávač nově rozlišuje mezi osobou, která zprávu odeslala, a osobou pouze zmíněnou v textu.
- Rozšířen výběr kandidátů kombinací sémantické podobnosti, známých odesílatelů a historie feedbacku.
- Přidáno tlačítko „Najít další“ pro procházení další várky kandidátních e-mailů.
- Přidán přehled uložených známých pojmů s možností jejich odstranění.
- Zachována vylepšená detekce odhlašovacích odkazů.

## 0.10.0

- Přepracováno AI vyhledávání na dvoustupňový systém.
- Embeddingy nyní slouží k rychlému výběru kandidátních e-mailů.
- Kandidátní e-maily následně kontroluje AI podle skutečného významu dotazu.
- Přidán AI reranking výsledků.
- Slabě nebo náhodně související e-maily mohou být z výsledků úplně vyřazeny.
- Odstraněno zobrazování neupravených útržků těla e-mailu ve výsledcích.
- Každý výsledek nyní obsahuje krátké AI shrnutí.
- Každý výsledek obsahuje vysvětlení, proč odpovídá dotazu.
- Sémantická shoda byla v uživatelském rozhraní nahrazena AI hodnocením relevance.
- Řazení podle relevance používá AI skóre relevance.
- Řazení „Nejnovější“ nejprve zachová pouze AI vyhodnocené relevantní zprávy a následně je seřadí podle data.
- Zachována vylepšená detekce odhlašovacích odkazů z verze 0.9.1.

## 0.9.1

- Opravena detekce odhlašovacích odkazů u newsletterů s obecným textem odkazu typu „zde“.
- Parser nově vyhodnocuje i okolní text odkazu.
- Přidána podpora výrazů „odhlášení“ a „odhlaseni“ v textu i URL.
- Rozšířena detekce odhlašovacích URL obsahujících například `/newsletter/odhlaseni`.
- Zachována konzervativní minimální hranice skóre, aby nedocházelo k falešné detekci běžných odkazů.

## 0.9.0

- Přidáno řazení výsledků AI vyhledávání podle relevance nebo data.
- Při řazení podle data se relevantní výsledky zobrazují od nejnovějších.
- Indexování e-mailů bylo změněno z pevného počtu zpráv na časové období.
- Přidány možnosti indexování za poslední měsíc, 6 měsíců, rok, 2 roky nebo celou schránku.
- Již indexované e-maily se při aktualizaci automaticky přeskočí.
- Opakované indexování stejného období doplní pouze nové zprávy.
- Před indexováním celé schránky se nově zobrazí potvrzení.
- Upraven text statistik indexování – místo „Projito“ se používá „Zkontrolováno“.

## 0.8.2

- Odstraněn duplicitní horní přehled počtu indexovaných e-mailů.
- AI vyhledávání se nyní zobrazuje bezprostředně pod nadpisem záložky.
- Informace o velikosti indexu zůstává pouze v sekci Index e-mailů.
- Zjednodušeno rozložení záložky AI vyhledávání.

## 0.8.1

- Přesunuto AI vyhledávání nad správu indexu.
- Vyhledávací pole je nyní dostupné ihned po otevření záložky.
- Indexování bylo přesunuto do spodní servisní části AI vyhledávání.
- Změněna logika indexování z počtu procházených zpráv na počet nově přidaných zpráv.
- Již indexované e-maily se při dalším indexování přeskočí.
- Po přeskočení již známých zpráv aplikace pokračuje dále do historie Gmailu.
- Volba „Přidat do indexu“ nyní znamená skutečný počet nových e-mailů.
- Přidán přehled počtu přeskočených a nově indexovaných zpráv.

## 0.8.0

- Přidáno AI vyhledávání v e-mailové schránce.
- Přidán lokální sémantický index e-mailů.
- Vyhledávání rozumí významu dotazu a není omezeno jen na přesná klíčová slova.
- Přidána nová záložka AI vyhledávání.
- Lze indexovat posledních 100, 250, 500 nebo 1000 e-mailů.
- Index zahrnuje přijaté e-maily z Inboxu i archivu.
- Spam, Koš, Odeslané a Koncepty se do indexu nezahrnují.
- Již indexované e-maily se při další aktualizaci znovu neposílají do embedding API.
- Přidáno průběžné doplňování nových zpráv do existujícího indexu.
- Přidán přehled počtu indexovaných e-mailů.
- Výsledky hledání jsou řazené podle sémantické podobnosti.
- U výsledků lze jedním kliknutím otevřít původní zprávu v Gmailu.
- E-mail přesunutý přes Inbox Assistant do koše se odstraní také z vyhledávacího indexu.
- Index a embeddingy jsou ukládány pouze lokálně v inbox_assistant.db.

## 0.7.0

- Zpřesněna AI klasifikace newsletterů a reklamních e-mailů.
- Marketingové a hromadné firemní zprávy se nyní méně často chybně řadí do kategorie Na vědomí.
- Přítomnost možnosti odhlášení je nově silným signálem pro klasifikaci newsletteru.
- Výrazně vylepšena detekce odhlašovacích odkazů v HTML e-mailu.
- Detekce nově kontroluje text odkazu, URL i HTML atributy.
- Přidána podpora marketingových a trackingových odhlašovacích URL.
- Přidána lokální historie odhlašování newsletterů.
- One-Click odhlášení se po úspěšném požadavku automaticky uloží do historie.
- U klasických webových odhlašovacích stránek lze dokončené odhlášení ručně označit.
- Nedávno řešené odhlášení se znovu zbytečně nenabízí.
- Výchozí platnost historie odhlášení je 30 dní.
- Platnost historie lze změnit v Nastavení.
- Historii odhlašování lze v Nastavení vypnout.
- U newsletteru bez nalezeného odhlašovacího odkazu se zobrazí informační zpráva.

## 0.6.1

- Opraveno chování tlačítka K řešení.
- E-mail se po označení jako K řešení okamžitě odstraní z aktuálního seznamu.
- Chování K řešení je nyní konzistentní se stavem Vyřešeno.

## 0.6.0

- Přidána lokální historie přesunů e-mailů do koše.
- Přidáno chytré přeskočení potvrzení u opakovaně mazaných odesílatelů.
- Porovnávání probíhá podle přesné e-mailové adresy odesílatele.
- Výchozí limit je 3 předchozí smazání během 30 dní.
- Samotné mazání zůstává vždy vyvolané ručním kliknutím na tlačítko Koš.
- Přidáno nové centrum Nastavení.
- V nastavení lze chytré potvrzování vypnout.
- Lze nastavit počet předchozích smazání i časové okno.
- Nastavení se ukládá lokálně a zachová se po restartu aplikace.

## 0.5.1

- Opravena podpora One-Click odhlášení při HTTP přesměrování 307/308.
- One-Click odhlášení nyní bezpečně následuje přesměrování se zachováním POST požadavku.
- Přidán limit počtu přesměrování při odhlašování newsletterů.
- Sidebar je při spuštění aplikace nově ve výchozím stavu sbalený.

## 0.5.0

- Vylepšeno odhlašování newsletterů.
- Přidána podpora standardu List-Unsubscribe-Post / One-Click.
- One-Click odhlášení nyní používá správný POST požadavek místo pouhého otevření odkazu.
- Před One-Click odhlášením se zobrazí potvrzení.
- Pokud newsletter nemá odhlašovací odkaz v hlavičkách e-mailu, aplikace ho zkusí najít přímo v HTML těle zprávy.
- Přidána podpora textových odkazů typu „Odhlásit odběr“, „Zrušit odběr“, „Unsubscribe“ a podobných.
- Přidána základní kontrola bezpečnosti URL před automatickým One-Click odhlášením.
- Odebrána sekce Roadmap ze sidebaru.
- Zjednodušen sidebar aplikace.

## 0.4.0

- Výchozí analýza nyní zobrazuje pouze neoznačené e-maily.
- E-maily označené jako K řešení nebo Vyřešeno se standardně přeskočí.
- Označené e-maily se nezapočítávají do zvoleného limitu analyzovaných zpráv.
- Přidána volba „Zobrazit i označené“.
- Stav Přečtené / Nepřečtené nemá vliv na filtrování e-mailů.

## 0.3.2

- Opravena chyba se sbaleným sidebarem.
- Sidebar se nyní správně chová při rozbalení a sbalení.
- Zmenšena typografie v changelogu a roadmapě.
- Zmenšena velikost nadpisů uvnitř sidebaru.
- Upraveno řádkování pro lepší přehlednost sidebaru.

## 0.3.1

- Rozšířen sidebar.
- Upraveno rozložení akčních tlačítek.
- Tlačítka jsou kompaktnější a zobrazují se v jednom řádku.
- Stav e-mailu se zobrazuje pomocí badge.
- Zkráceny názvy některých tlačítek.

## 0.3.0

- Přidán stav Přečtené / Nepřečtené.
- Přidán štítek K řešení.
- Stav Vyřešeno automaticky označí e-mail jako přečtený.
- Přidána možnost vrátit e-mail do stavu Nevyřešeno.

## 0.2.0

- Přidáno grafické rozhraní ve Streamlitu.
- Přidáno otevření konkrétního e-mailu v Gmailu.
- Přidán odkaz pro odhlášení newsletteru.
- Přidán přesun e-mailu do koše s potvrzením.
- Přidána volba počtu analyzovaných e-mailů.
- Přidán stav Vyřešeno.

## 0.1.0

- Připojení ke Gmail API.
- OAuth přihlášení.ß
- Napojení na OpenAI API.
- AI shrnutí e-mailů.
- Kategorizace, priorita a doporučená akce.