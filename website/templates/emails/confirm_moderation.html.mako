<%inherit file="notify_base.mako" />

<%def name="content()">
<tr>
  <td style="border-collapse: collapse;">
    Hello ${user.fullname},<br>
    <br>
    You have been added by ${referrer.fullname}, as ${'an administrator' if is_admin else 'a moderator'} to ${provider.name}, powered by GRDM. To set a password for your account, visit:<br>
    <br>
    ${claim_url}<br>
    <br>
    Once you have set a password you will be able to moderate submissions and create your own ${provider.preprint_word}. You will automatically be subscribed to notification emails for new ${provider.preprint_word} submissions to ${provider.name}.<br>
    <br>
    If you are not ${user.fullname} or you have been erroneously associated with ${provider.name}, email contact+${provider._id}@rdm.nii.ac.jp with the subject line "Claiming error" to report the problem.<br>
    <br>
    Sincerely,<br>
    Your ${provider.name} and GRDM teams<br>
</tr>
</%def>
