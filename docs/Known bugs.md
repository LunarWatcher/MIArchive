# Known bugs

## Infinite loading caused by sandboxing

On `stackoverflow.com/questions`, a hidden dialog contains an image that doesn't load during the scraping process. This results in a 404, which result in an error, which triggers a callback that reloads the image. In Chrome, this results in hundreds of thousands of requests per minute. In Firefox, thousands to tens of thousands. 

This is caused by a peculiar set of circumstances that I do not understand. Specifically:

* This is not supposed to happen, because as far as I can tell, a script is supposed to run that hides it or something to that effect. Unfortunately, it tries to access `document`, and fails. This makes no sense to me, since the sandbox is still supposed to have its own `document`
* This failure makes no sense, since another root-level `<script>` loads even the exact same code without issue. Neither of the scripts have any special attributes. 
* I half suspect it's something weird with how scripts are treated, but I cannot narrow it down. All I know is that it fails with `sandbox allow-scripts`
    * For obvious reasons, it doesn't fail without `allow-scripts`, because that prevents any of the scripts from loading in the first place, including the script that assembles the dialog.
* The failure mode also happens in a `sandbox`ed `<iframe>`, because CSP and iframe's sandboxes are fairly similar. 


**Workaround:** added `/noscript/web/`, which is identical to `/web/`, except disallowing `allow-scripts` in the sandbox. The JS version still loads infinitely.

**Planned pseudo-resolution:** Some form of scraper plugin that allows finer-grained control of the archival process, with a default for the SE sites that blocks the signup script. This may also be achieved through ublock.

**Fixable?** Maybe, but I don't know how. The only fix seems to be unsandboxing and relying on CORS, and CORS is a piece of shit
