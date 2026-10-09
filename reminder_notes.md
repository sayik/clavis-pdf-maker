### Commands
- This long command because bash windows incompatability






## Reminders 
- Presigned url needs to be matched with user id so lambda must receive that too
- 



## To-Test
- Build the image and make sure WeasyPrint's native dependencies and fonts are installed inside the container. ✔️
- Run the renderer locally using your sample JSON and verify the PDF looks identical to your expected output.
- Keep assets self-contained — HTML templates, CSS, SVGs, logo and fonts should all be packaged inside the image.
- Test variable-length reports — long medication lists, many lab results, lengthy notes, and reports that need three or more pages.
- Test S3 uploads separately using a presigned URL, then integrate that step into the service.


## Lambda 
- How is it initiated, set scaling 
- How is it run over http request - currently its expecting internal connections
- lambda encryption is necessary